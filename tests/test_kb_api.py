import shutil
import unittest
from pathlib import Path

from dotenv import load_dotenv
from fastapi.testclient import TestClient

from langchain_ai_agent.api.main import app
from langchain_ai_agent.retriever.vector_store import DocumentEmbedder

load_dotenv()


class TestKnowledgeBaseAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.faiss_index_dir = Path("faiss_index/default")
        self.sample_doc = Path("tests/kb_api_doc.txt")
        self.sample_doc.parent.mkdir(parents=True, exist_ok=True)
        self.sample_doc.write_text("knowledge base document", encoding="utf-8")

        embedder = DocumentEmbedder(persist_dir=str(self.faiss_index_dir))
        embedder.build_or_update_index(
            [
                {
                    "chunk_id": 0,
                    "text": "knowledge base document",
                    "filename": self.sample_doc.name,
                    "source_type": "txt",
                    "doc_path": str(self.sample_doc),
                }
            ]
        )

    def tearDown(self):
        if self.sample_doc.exists():
            self.sample_doc.unlink()
        if self.faiss_index_dir.exists():
            shutil.rmtree(self.faiss_index_dir)

    def test_list_documents(self):
        response = self.client.get("/api/kb/documents")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data["documents"]), 1)
        self.assertEqual(data["documents"][0]["filename"], self.sample_doc.name)

    def test_delete_document(self):
        response = self.client.delete(
            f"/api/kb/documents/{self.sample_doc.name}",
            params={"doc_path": str(self.sample_doc)},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["remaining_documents"], 0)

    def test_rebuild_document_index(self):
        response = self.client.post("/api/kb/rebuild")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["rebuilt_documents"], 1)


if __name__ == "__main__":
    unittest.main()
