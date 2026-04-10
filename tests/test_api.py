# tests/test_api.py

import unittest
from fastapi.testclient import TestClient
from langchain_ai_agent.api.main import app
from dotenv import load_dotenv

load_dotenv()


class TestAgentAPI(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_run_agent_valid(self):
        payload = {
            "text": (
                "This meeting note covers the Q2 roadmap. The team agreed to improve onboarding, "
                "add Slack integration, and reduce churn by 20%. Sarah will lead onboarding."
            )
        }

        response = self.client.post("/run-agent", json=payload)
        self.assertEqual(response.status_code, 200)

        data = response.json()
        self.assertIn("task", data)
        self.assertIn("output", data)
        self.assertIn("agent_trace", data)
        self.assertIsInstance(data["task"], str)
        self.assertIsInstance(data["output"], dict)

        # Check memory feedback injection
        self.assertIn("similar_cases", data["agent_trace"])
        self.assertIsInstance(data["agent_trace"]["similar_cases"], list)

    def test_run_agent_empty_text(self):
        payload = {"text": "   "}
        response = self.client.post("/run-agent", json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("Input must contain non-empty", response.text)

    def test_run_agent_missing_text(self):
        response = self.client.post("/run-agent", json={})
        self.assertEqual(response.status_code, 422)  # Validation error for missing required field


if __name__ == "__main__":
    unittest.main()
