# tests/test_run_ingestion_pipeline.py

import unittest
from fastapi.testclient import TestClient
from langchain_ai_agent.api.main import app
from pathlib import Path
import shutil
import os
from dotenv import load_dotenv

load_dotenv()

class TestRunIngestionPipeline(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

        # Create temp dir and test file
        self.test_dir = Path("tests/tmp_ingest_dir")
        self.test_dir.mkdir(parents=True, exist_ok=True)
        self.test_file = self.test_dir / "test_doc.txt"
        self.test_file.write_text("This is a test document for ingestion.")

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)
        faiss_ns = Path("faiss_index/default")
        if faiss_ns.exists():
            shutil.rmtree(faiss_ns)

    def test_run_ingestion_pipeline_success(self):
        response = self.client.post("/run-ingestion-pipeline", params={
            "path": str(self.test_dir),
            "namespace": "default"
        })

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertIn("num_chunks", data)
        self.assertGreater(data["num_chunks"], 0)
        self.assertEqual(data["namespace"], "default")

    def test_run_ingestion_pipeline_invalid_path(self):
        response = self.client.post("/run-ingestion-pipeline", params={
            "path": "invalid/path/doesnotexist",
            "namespace": "default"
        })

        self.assertEqual(response.status_code, 500)
        self.assertIn("detail", response.json())

    def test_run_ingestion_pipeline_missing_path(self):
        response = self.client.post("/run-ingestion-pipeline", params={
            "namespace": "default"
        })

        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
