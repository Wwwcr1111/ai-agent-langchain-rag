# tests/test_memory_store.py

import unittest
import shutil
from pathlib import Path
from langchain_ai_agent.feedback_loop.memory_store import MemoryStore
from dotenv import load_dotenv

load_dotenv()


class TestMemoryStore(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path("tests/temp_memory_store")
        self.store = MemoryStore(persist_dir=str(self.test_dir))

        self.sample_input = "Customer reported issues with logging into the dashboard."
        self.sample_output = {
            "category": "account",
            "urgency": "high",
            "route_to": "Level 2 Support",
            "explanation": "High urgency login issue routed to Level 2."
        }
        self.task = "triage"
        self.meta = {
            "filename": "support_ticket_001.txt",
            "chunk_id": 0
        }

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_add_experience_and_query(self):
        self.store.add_experience(
            input_text=self.sample_input,
            output=self.sample_output,
            task=self.task,
            metadata=self.meta
        )

        results = self.store.query_similar(self.sample_input, k=1)
        self.assertEqual(len(results), 1)

        result = results[0]
        self.assertIn("metadata", result)
        self.assertIn("text", result)
        self.assertEqual(result["metadata"]["task"], self.task)
        self.assertIn("output", result["metadata"])
        self.assertEqual(result["metadata"]["filename"], self.meta["filename"])

    def test_query_no_data(self):
        empty_dir = Path("tests/empty_memory_store")
        empty_store = MemoryStore(persist_dir=str(empty_dir))

        results = empty_store.query_similar("Unseen input", k=1)
        self.assertEqual(results, [])

        shutil.rmtree(empty_dir)

    def test_invalid_experience_structure(self):
        with self.assertLogs(level='ERROR') as cm:
            self.store.add_experience(input_text="", output={}, task="", metadata={})
            self.assertTrue(any("Experience validation failed" in msg for msg in cm.output))


if __name__ == "__main__":
    unittest.main()
