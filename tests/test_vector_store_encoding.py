import json
import shutil
import sys
import types
import unittest
from pathlib import Path


community_module = types.ModuleType("langchain_community")
vectorstores_module = types.ModuleType("langchain_community.vectorstores")
embeddings_module = types.ModuleType("langchain_community.embeddings")


class FAISS:
    @classmethod
    def load_local(cls, *args, **kwargs):
        return cls()

    @classmethod
    def from_documents(cls, *args, **kwargs):
        return cls()

    def save_local(self, *args, **kwargs):
        return None


class HuggingFaceEmbeddings:
    def __init__(self, *args, **kwargs):
        pass


vectorstores_module.FAISS = FAISS
embeddings_module.HuggingFaceEmbeddings = HuggingFaceEmbeddings
community_module.vectorstores = vectorstores_module
community_module.embeddings = embeddings_module
sys.modules.setdefault("langchain_community", community_module)
sys.modules.setdefault("langchain_community.vectorstores", vectorstores_module)
sys.modules.setdefault("langchain_community.embeddings", embeddings_module)

docstore_module = types.ModuleType("langchain.docstore.document")


class Document:
    def __init__(self, page_content, metadata):
        self.page_content = page_content
        self.metadata = metadata


docstore_module.Document = Document
sys.modules.setdefault("langchain.docstore.document", docstore_module)

retrievers_module = types.ModuleType("langchain_core.retrievers")


class BaseRetriever:
    pass


retrievers_module.BaseRetriever = BaseRetriever
sys.modules.setdefault("langchain_core.retrievers", retrievers_module)

from langchain_ai_agent.retriever.vector_store import DocumentEmbedder


class TestVectorStoreEncoding(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path("tests/tmp_vector_encoding")
        self.test_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def _build_embedder(self) -> DocumentEmbedder:
        embedder = object.__new__(DocumentEmbedder)
        embedder._persist_dir = self.test_dir
        embedder._metadata_file = self.test_dir / "metadata.jsonl"
        embedder._documents_file = self.test_dir / "documents.jsonl"
        return embedder

    def test_load_existing_metadata_reads_utf8_jsonl(self):
        metadata_file = self.test_dir / "metadata.jsonl"
        metadata_rows = [
            {
                "chunk_id": 0,
                "filename": "扫地机器人说明书.pdf",
                "source_type": "pdf",
                "doc_path": "tmp_uploads/扫地机器人说明书.pdf",
            }
        ]
        metadata_file.write_text(
            "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in metadata_rows),
            encoding="utf-8",
        )

        embedder = self._build_embedder()
        loaded = embedder._load_existing_metadata()

        self.assertEqual(loaded, metadata_rows)

    def test_load_registered_documents_reads_utf8_sig_jsonl(self):
        documents_file = self.test_dir / "documents.jsonl"
        records = [
            {
                "filename": "扫地机器人说明书.pdf",
                "source_type": "pdf",
                "doc_path": "tmp_uploads/扫地机器人说明书.pdf",
            }
        ]
        documents_file.write_text(
            "\ufeff" + "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in records),
            encoding="utf-8",
        )

        embedder = self._build_embedder()
        loaded = embedder._load_registered_documents()

        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0].filename, "扫地机器人说明书.pdf")
