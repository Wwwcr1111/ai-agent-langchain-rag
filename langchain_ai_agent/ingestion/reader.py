import json
import logging
from pathlib import Path
from typing import Any, Dict, List
import yaml

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, TextLoader
from unstructured.partition.auto import partition


# Setup logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

class DocumentIngestor:
    def __init__(self, config_path: str | None = None):
        if config_path is None:
            config_path = str(Path(__file__).resolve().parent.parent / "config" / "ingestion_config.yml")
        self.config = self._load_config(config_path)
        self.chunk_size = self.config.get("chunk_size", 500)
        self.chunk_overlap = self.config.get("chunk_overlap", 50)
        configured_extensions = self.config.get(
            "supported_extensions",
            [".pdf", ".docx", ".txt", ".md", ".json", ".jsonl", ".eml", ".html"],
        )
        self.supported_extensions = {extension.lower() for extension in configured_extensions}
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size,
            chunk_overlap=self.chunk_overlap
        )

    def _load_config(self, path: str) -> Dict:
        try:
            with open(path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.warning(f"No config file found at {path}, using defaults.")
            return {}

    def _load_pdf_text(self, filepath: Path) -> str:
        documents = PyPDFLoader(str(filepath)).load()
        return "\n".join(doc.page_content for doc in documents if doc.page_content)

    def _load_text_document(self, filepath: Path) -> str:
        documents = TextLoader(str(filepath), encoding="utf-8").load()
        return "\n".join(doc.page_content for doc in documents if doc.page_content)

    def _json_value_to_text(self, value: Any) -> str:
        if isinstance(value, str):
            return value
        return json.dumps(value, ensure_ascii=False, indent=2)

    def _load_json_document(self, filepath: Path) -> str:
        with open(filepath, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
        return self._json_value_to_text(data)

    def _load_jsonl_document(self, filepath: Path) -> str:
        rows: List[str] = []
        with open(filepath, "r", encoding="utf-8-sig") as f:
            for line in f:
                if not line.strip():
                    continue
                rows.append(self._json_value_to_text(json.loads(line)))
        return "\n".join(rows)

    def _load_unstructured_document(self, filepath: Path) -> str:
        elements = partition(filename=str(filepath))
        return "\n".join([el.text for el in elements if hasattr(el, "text") and el.text])

    def _extract_text_by_type(self, filepath: Path) -> str:
        suffix = filepath.suffix.lower()
        if suffix == ".pdf":
            return self._load_pdf_text(filepath)
        if suffix in {".txt", ".md"}:
            return self._load_text_document(filepath)
        if suffix == ".json":
            return self._load_json_document(filepath)
        if suffix == ".jsonl":
            return self._load_jsonl_document(filepath)
        return self._load_unstructured_document(filepath)

    def _extract_text(self, filepath: Path) -> str:
        try:
            return self._extract_text_by_type(filepath)
        except Exception as e:
            logger.error(f"[Ingestor] Failed to parse {filepath.name}: {e}")
            return ""
        
    def _is_supported(self, filepath: Path) -> bool:
        return filepath.suffix.lower() in self.supported_extensions

    def process_file(self, filepath: Path) -> List[Dict]:
        if not self._is_supported(filepath):
            logger.warning(f"[Ingestor] Skipping unsupported file type: {filepath.name}")
            return []
        
        logger.info(f"[Ingestor] Processing file: {filepath.name}")
        raw_text = self._extract_text(filepath)

        if not raw_text.strip():
            logger.warning(f"[Ingestor] No text extracted from {filepath.name}")
            return []

        chunks = self.text_splitter.split_text(raw_text)

        return [
            {"chunk_id": i,
             "text": chunk,
             "doc_path": str(filepath),
             "filename": filepath.name,
             "source_type": filepath.suffix.lstrip(".").lower()}

            for i, chunk in enumerate(chunks)
        ]
    
    def process_directory(self, folder_path: Path) -> List[Dict]:
        all_chunks = []
        for file_path in folder_path.glob("**/*"):
            if file_path.is_file():
                chunks = self.process_file(file_path)
                all_chunks.extend(chunks)
        logger.info(f"[Ingestor] Finished processing directory: {folder_path}")
        return all_chunks

def ingest_and_chunk(path: str) -> dict:
    # example dummy logic
    return {"status": "ingested", "path": path}
