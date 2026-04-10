import json
import logging
from typing import List, Dict, Optional, Any
from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.docstore.document import Document
from pydantic import BaseModel, PrivateAttr, ValidationError
from langchain_core.retrievers import BaseRetriever

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class ChunkMetadata(BaseModel):
    chunk_id: int
    text: str
    filename: str
    source_type: str
    doc_path: str


class DocumentRecord(BaseModel):
    filename: str
    source_type: str
    doc_path: str


class DocumentSummary(DocumentRecord):
    chunk_count: int = 0
    missing: bool = False


class DocumentEmbedder(BaseRetriever, BaseModel):
    # Public fields, part of the retriever's configuration.
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    persist_dir: str = "faiss_index"

    # Private attributes that will not be part of the Pydantic model
    _persist_dir: Path = PrivateAttr()
    _metadata_file: Path = PrivateAttr()
    _documents_file: Path = PrivateAttr()
    _embedding_function: Any = PrivateAttr()
    _vector_store: Optional[Any] = PrivateAttr(default=None)

    def __init__(self, **data):
        super().__init__(**data)
        # Convert the persist_dir (a string) into a Path object and store it as a private attribute.
        self._persist_dir = Path(self.persist_dir)
        self._metadata_file = self._persist_dir / "metadata.jsonl"
        self._documents_file = self._persist_dir / "documents.jsonl"
        self._embedding_function = HuggingFaceEmbeddings(model_name=self.model_name)
        
        # Create the directory if it doesn't exist; otherwise try to load the FAISS index.
        if not self._persist_dir.exists():
            self._persist_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"[Embedder] Initialized new FAISS index directory: {self._persist_dir}")
        else:
            self._load_faiss()

    def _load_faiss(self):
        try:
            self._vector_store = FAISS.load_local(
                folder_path=str(self._persist_dir),
                embeddings=self._embedding_function,
                allow_dangerous_deserialization=True
            )
            logger.info("[Embedder] Loaded FAISS index from disk.")
        except Exception as e:
            logger.error(f"[Embedder] Failed to load FAISS index: {e}")
            # The existing index file might be corrupted or incompatible.
            # Remove all files in the persist directory to force a rebuild.
            try:
                for file in self._persist_dir.iterdir():
                    file.unlink()
                logger.info("[Embedder] Removed corrupted FAISS index files from disk.")
            except Exception as remove_error:
                logger.error(f"[Embedder] Failed to remove corrupted FAISS index files: {remove_error}")
            # Set the vector store to None so that downstream queries fail fast
            # and a new index can be built by calling build_or_update_index.
            self._vector_store = None


    def _load_existing_metadata(self) -> List[Dict]:
        if self._metadata_file.exists():
            with open(self._metadata_file, "r", encoding="utf-8-sig") as f:
                return [json.loads(line) for line in f if line.strip()]
        return []

    def _write_metadata(self, metadata: List[Dict]):
        if not metadata:
            if self._metadata_file.exists():
                self._metadata_file.unlink()
            return

        with open(self._metadata_file, "w", encoding="utf-8") as f:
            for record in metadata:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def _append_metadata(self, metadata: List[Dict]):
        with open(self._metadata_file, "a", encoding="utf-8") as f:
            for record in metadata:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def _load_registered_documents(self) -> List[DocumentRecord]:
        if self._documents_file.exists():
            with open(self._documents_file, "r", encoding="utf-8-sig") as f:
                return [DocumentRecord(**json.loads(line)) for line in f if line.strip()]

        records: List[DocumentRecord] = []
        seen_keys: set[tuple[str, str]] = set()
        for item in self._load_existing_metadata():
            key = (item["filename"], item["doc_path"])
            if key in seen_keys:
                continue
            seen_keys.add(key)
            records.append(
                DocumentRecord(
                    filename=item["filename"],
                    source_type=item["source_type"],
                    doc_path=item["doc_path"],
                )
            )
        return records

    def _write_registered_documents(self, records: List[DocumentRecord]):
        if not records:
            if self._documents_file.exists():
                self._documents_file.unlink()
            return

        with open(self._documents_file, "w", encoding="utf-8") as f:
            for record in records:
                f.write(json.dumps(record.model_dump(), ensure_ascii=False) + "\n")

    def _deduplicate_document_records(self, records: List[DocumentRecord]) -> List[DocumentRecord]:
        deduplicated: List[DocumentRecord] = []
        seen_keys: set[tuple[str, str]] = set()
        for record in records:
            key = (record.filename, record.doc_path)
            if key in seen_keys:
                continue
            seen_keys.add(key)
            deduplicated.append(record)
        return deduplicated

    def _clear_vector_store_files(self):
        for filename in ("index.faiss", "index.pkl"):
            file_path = self._persist_dir / filename
            if file_path.exists():
                file_path.unlink()
        self._vector_store = None

    def _save_documents(self, documents: List[Document]):
        if not documents:
            self._clear_vector_store_files()
            return

        self._vector_store = FAISS.from_documents(documents, self._embedding_function)
        self._vector_store.save_local(str(self._persist_dir))

    def _build_documents_from_chunks(self, chunks: List[ChunkMetadata]) -> List[Document]:
        return [
            Document(
                page_content=chunk.text,
                metadata={
                    "chunk_id": chunk.chunk_id,
                    "filename": chunk.filename,
                    "source_type": chunk.source_type,
                    "doc_path": chunk.doc_path,
                },
            )
            for chunk in chunks
        ]

    def _validate_chunks(self, chunk_data: List[Dict]) -> List[ChunkMetadata]:
        validated_chunks = []
        for i, item in enumerate(chunk_data):
            if not isinstance(item, dict):
                logger.warning(f"[Embedder] Skipping non-dict chunk at index {i}: {item}")
                continue
            try:
                validated_chunks.append(ChunkMetadata(**item))
            except ValidationError as e:
                logger.error(f"[Embedder] Invalid chunk at index {i}: {e}")
                raise
        return validated_chunks

    def register_documents(self, records: List[Dict | DocumentRecord]):
        existing_records = self._load_registered_documents()
        new_records = [
            record if isinstance(record, DocumentRecord) else DocumentRecord(**record)
            for record in records
        ]
        merged_records = self._deduplicate_document_records(existing_records + new_records)
        self._write_registered_documents(merged_records)

    def list_documents(self) -> List[Dict]:
        metadata = self._load_existing_metadata()
        chunk_counts: Dict[tuple[str, str], int] = {}
        for item in metadata:
            key = (item["filename"], item["doc_path"])
            chunk_counts[key] = chunk_counts.get(key, 0) + 1

        summaries = [
            DocumentSummary(
                filename=record.filename,
                source_type=record.source_type,
                doc_path=record.doc_path,
                chunk_count=chunk_counts.get((record.filename, record.doc_path), 0),
                missing=not Path(record.doc_path).exists(),
            )
            for record in self._load_registered_documents()
        ]
        summaries.sort(key=lambda item: item.filename.lower())
        return [summary.model_dump() for summary in summaries]

    def rebuild_index(self, chunk_data: List[Dict], records: List[DocumentRecord]):
        validated_chunks = self._validate_chunks(chunk_data)
        documents = self._build_documents_from_chunks(validated_chunks)
        self._save_documents(documents)
        self._write_metadata([doc.metadata for doc in documents])
        self._write_registered_documents(self._deduplicate_document_records(records))

    def rebuild_from_documents(self, ingestor) -> Dict[str, Any]:
        rebuilt_records: List[DocumentRecord] = []
        skipped_files: List[Dict[str, str]] = []
        all_chunks: List[Dict] = []

        for record in self._load_registered_documents():
            file_path = Path(record.doc_path)
            if not file_path.exists():
                skipped_files.append({"filename": record.filename, "doc_path": record.doc_path})
                continue

            chunks = ingestor.process_file(file_path)
            if not chunks:
                skipped_files.append({"filename": record.filename, "doc_path": record.doc_path})
                continue

            rebuilt_records.append(record)
            all_chunks.extend(chunks)

        self.rebuild_index(all_chunks, rebuilt_records)
        return {
            "rebuilt_documents": len(rebuilt_records),
            "num_chunks": len(all_chunks),
            "skipped_files": skipped_files,
        }

    def delete_document(self, filename: str, doc_path: str, ingestor) -> Dict[str, Any]:
        existing_records = self._load_registered_documents()
        remaining_records = [
            record
            for record in existing_records
            if not (record.filename == filename and record.doc_path == doc_path)
        ]

        if len(remaining_records) == len(existing_records):
            raise FileNotFoundError(f"Document not found: {filename}")

        self._write_registered_documents(remaining_records)
        rebuild_result = self.rebuild_from_documents(ingestor)
        rebuild_result["deleted"] = {"filename": filename, "doc_path": doc_path}
        rebuild_result["remaining_documents"] = len(self._load_registered_documents())
        return rebuild_result

    def _deduplicate_chunks(
        self,
        new_chunks: List[ChunkMetadata],
        existing_metadata: List[Dict]
    ) -> List[ChunkMetadata]:
        existing_keys = {
            (item["chunk_id"], item["filename"])
            for item in existing_metadata
        }
        filtered = [
            chunk for chunk in new_chunks
            if (chunk.chunk_id, chunk.filename) not in existing_keys
        ]
        return filtered

    def build_or_update_index(self, chunk_data: List[Dict]):
        if not chunk_data:
            raise ValueError("[Embedder] No chunks provided.")

        validated_chunks = self._validate_chunks(chunk_data)

        existing_metadata = self._load_existing_metadata()
        new_chunks = self._deduplicate_chunks(validated_chunks, existing_metadata)

        if not new_chunks:
            logger.info("[Embedder] No new unique chunks to index.")
            return

        documents = self._build_documents_from_chunks(new_chunks)

        if self._vector_store:
            self._vector_store.add_documents(documents)
            logger.info(f"[Embedder] Appended {len(documents)} new documents to existing index.")
        else:
            self._vector_store = FAISS.from_documents(documents, self._embedding_function)
            logger.info(f"[Embedder] Created new FAISS index with {len(documents)} documents.")

        self._vector_store.save_local(str(self._persist_dir))
        self._append_metadata([doc.metadata for doc in documents])
        self.register_documents(
            [
                {
                    "filename": doc.metadata["filename"],
                    "source_type": doc.metadata["source_type"],
                    "doc_path": doc.metadata["doc_path"],
                }
                for doc in documents
            ]
        )

    def get_retriever(self, k: int = 4):
        if self._vector_store is None:
            raise ValueError("[Embedder] Vector store not initialized.")
        return self._vector_store.as_retriever(search_kwargs={"k": k})

    def query(self, question: str, k: int = 4) -> List[Document]:
        retriever = self.get_retriever(k=k)
        docs = retriever.get_relevant_documents(question)
        logger.info(f"[Embedder] Retrieved {len(docs)} relevant documents for query.")
        return docs

    # Required by BaseRetriever: a synchronous method accepting a string and returning documents.
    def _get_relevant_documents(self, query: str) -> List[Document]:
        retriever = self.get_retriever(k=4)
        docs = retriever.get_relevant_documents(query)
        logger.info(f"[Embedder] Retrieved {len(docs)} relevant documents for query.")
        return docs

    # Optional asynchronous version.
    async def _aget_relevant_documents(self, query: str) -> List[Document]:
        retriever = self.get_retriever(k=4)
        docs = await retriever.aget_relevant_documents(query)
        logger.info(f"[Embedder] Retrieved {len(docs)} relevant documents for query (async).")
        return docs
