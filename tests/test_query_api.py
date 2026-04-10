# tests/test_query_api.py

import unittest
from fastapi.testclient import TestClient
from langchain_ai_agent.api.main import app
from dotenv import load_dotenv

load_dotenv()


class TestQueryAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_query_kb_valid(self):
        response = self.client.get("/api/query", params={
            "question": "Where is Boston?",
            "namespace": "default"
        })

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("results", data)
        self.assertIn("sources", data)
        self.assertIsInstance(data["results"], list)
        self.assertIsInstance(data["sources"], list)
        self.assertGreater(len(data["results"][0]), 5)  # basic sanity check

    def test_query_kb_missing_question(self):
        response = self.client.get("/api/query", params={"namespace": "default"})
        self.assertEqual(response.status_code, 422)  # Missing required query param

    def test_query_kb_invalid_namespace(self):
        response = self.client.get("/api/query", params={
            "question": "Who am I?",
            "namespace": "nonexistent_ns"
        })

        # The system should handle a missing FAISS index gracefully, or fail with 500
        self.assertIn(response.status_code, [200, 500])


if __name__ == "__main__":
    unittest.main()
