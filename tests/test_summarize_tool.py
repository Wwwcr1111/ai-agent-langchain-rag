# tests/test_summarize_tool.py

import unittest
from langchain_ai_agent.agents.tools.summarize_tool import summarizer_chain
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class TestSummarizeTool(unittest.TestCase):
    def setUp(self):
        self.valid_note = {
            "text": (
                "Team met to discuss Q2 product roadmap. John presented customer feedback analysis. "
                "Main goals include improving onboarding, adding integration with Slack, and reducing churn. "
                "Sarah will lead the onboarding revamp, due by May 15. Next check-in scheduled for next Tuesday."
            )
        }
        self.empty_note = {"text": ""}

    def test_summary_output_format(self):
        output = summarizer_chain.invoke(self.valid_note)

        self.assertIn("summary", output)
        self.assertIn("bullet_points", output)
        self.assertIsInstance(output["summary"], str)
        self.assertIsInstance(output["bullet_points"], list)
        self.assertGreater(len(output["summary"]), 20)
        self.assertGreaterEqual(len(output["bullet_points"]), 2)

        logger.info(f"[Test Output] {output}")

    def test_invalid_input_raises(self):
        with self.assertRaises(ValueError):
            summarizer_chain.invoke(self.empty_note)


if __name__ == "__main__":
    unittest.main()
