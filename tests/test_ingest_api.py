import io
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient


langchain_module = types.ModuleType("langchain")
text_splitter_module = types.ModuleType("langchain.text_splitter")


class RecursiveCharacterTextSplitter:
    def __init__(self, chunk_size, chunk_overlap):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def split_text(self, text):
        return [text] if text else []


text_splitter_module.RecursiveCharacterTextSplitter = RecursiveCharacterTextSplitter
langchain_module.text_splitter = text_splitter_module
sys.modules.setdefault("langchain", langchain_module)
sys.modules.setdefault("langchain.text_splitter", text_splitter_module)

community_module = types.ModuleType("langchain_community")
document_loaders_module = types.ModuleType("langchain_community.document_loaders")
vectorstores_module = types.ModuleType("langchain_community.vectorstores")
embeddings_module = types.ModuleType("langchain_community.embeddings")


class _LoaderStub:
    def __init__(self, *args, **kwargs):
        pass

    def load(self):
        return []


class FAISS:
    @classmethod
    def load_local(cls, *args, **kwargs):
        return cls()

    @classmethod
    def from_documents(cls, *args, **kwargs):
        return cls()

    def save_local(self, *args, **kwargs):
        return None

    def add_documents(self, *args, **kwargs):
        return None


class HuggingFaceEmbeddings:
    def __init__(self, *args, **kwargs):
        pass


document_loaders_module.PyPDFLoader = _LoaderStub
document_loaders_module.TextLoader = _LoaderStub
vectorstores_module.FAISS = FAISS
embeddings_module.HuggingFaceEmbeddings = HuggingFaceEmbeddings
community_module.document_loaders = document_loaders_module
community_module.vectorstores = vectorstores_module
community_module.embeddings = embeddings_module
sys.modules.setdefault("langchain_community", community_module)
sys.modules.setdefault("langchain_community.document_loaders", document_loaders_module)
sys.modules.setdefault("langchain_community.vectorstores", vectorstores_module)
sys.modules.setdefault("langchain_community.embeddings", embeddings_module)

unstructured_module = types.ModuleType("unstructured")
partition_pkg = types.ModuleType("unstructured.partition")
partition_auto_module = types.ModuleType("unstructured.partition.auto")
partition_auto_module.partition = lambda filename: []
partition_pkg.auto = partition_auto_module
unstructured_module.partition = partition_pkg
sys.modules.setdefault("unstructured", unstructured_module)
sys.modules.setdefault("unstructured.partition", partition_pkg)
sys.modules.setdefault("unstructured.partition.auto", partition_auto_module)

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

from langchain_ai_agent.api import ingest_api


class TestIngestAPI(unittest.TestCase):
    def setUp(self):
        self.app = FastAPI()
        self.app.include_router(ingest_api.router)
        self.client = TestClient(self.app)
        self.upload_dir = Path("tmp_uploads")

    def tearDown(self):
        if self.upload_dir.exists():
            for path in self.upload_dir.iterdir():
                path.unlink()
            self.upload_dir.rmdir()

    @patch("langchain_ai_agent.api.ingest_api.DocumentEmbedder")
    @patch("langchain_ai_agent.api.ingest_api.DocumentIngestor")
    def test_ingest_txt_success(self, mock_ingestor_cls, mock_embedder_cls):
        mock_ingestor_cls.return_value.process_file.return_value = [
            {
                "chunk_id": 0,
                "text": "sample text",
                "doc_path": "tmp_uploads/sample_ingest.txt",
                "filename": "sample_ingest.txt",
                "source_type": "txt",
            }
        ]

        response = self.client.post(
            "/api/ingest",
            files={"files": ("sample_ingest.txt", io.BytesIO(b"sample text"), "text/plain")},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "success")
        mock_ingestor_cls.return_value.process_file.assert_called_once()
        mock_embedder_cls.return_value.build_or_update_index.assert_called_once()

    @patch("langchain_ai_agent.api.ingest_api.DocumentEmbedder")
    @patch("langchain_ai_agent.api.ingest_api.DocumentIngestor")
    def test_ingest_md_success(self, mock_ingestor_cls, mock_embedder_cls):
        mock_ingestor_cls.return_value.process_file.return_value = [
            {
                "chunk_id": 0,
                "text": "# heading",
                "doc_path": "tmp_uploads/guide.md",
                "filename": "guide.md",
                "source_type": "md",
            }
        ]

        response = self.client.post(
            "/api/ingest",
            files={"files": ("guide.md", io.BytesIO(b"# heading"), "text/markdown")},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["namespace"], "default")
        mock_embedder_cls.return_value.build_or_update_index.assert_called_once()

    @patch("langchain_ai_agent.api.ingest_api.DocumentEmbedder")
    @patch("langchain_ai_agent.api.ingest_api.DocumentIngestor")
    def test_ingest_jsonl_success(self, mock_ingestor_cls, mock_embedder_cls):
        mock_ingestor_cls.return_value.process_file.return_value = [
            {
                "chunk_id": 0,
                "text": '{"page": 1, "text": "第一页"}',
                "doc_path": "tmp_uploads/manual.jsonl",
                "filename": "manual.jsonl",
                "source_type": "jsonl",
            }
        ]

        response = self.client.post(
            "/api/ingest",
            files={"files": ("manual.jsonl", io.BytesIO(b'{\"page\": 1}\n'), "application/json")},
        )

        self.assertEqual(response.status_code, 200)
        self.assertGreater(response.json()["num_chunks"], 0)
        mock_embedder_cls.return_value.build_or_update_index.assert_called_once()

    @patch("langchain_ai_agent.api.ingest_api.DocumentEmbedder")
    @patch("langchain_ai_agent.api.ingest_api.DocumentIngestor")
    def test_ingest_empty_file(self, mock_ingestor_cls, mock_embedder_cls):
        mock_ingestor_cls.return_value.process_file.return_value = []

        response = self.client.post(
            "/api/ingest",
            files={"files": ("empty.txt", io.BytesIO(b""), "text/plain")},
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn("No valid chunks", response.json()["detail"])
        mock_embedder_cls.return_value.build_or_update_index.assert_not_called()

    def test_ingest_missing_file(self):
        response = self.client.post("/api/ingest", files={})
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
