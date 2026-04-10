# tests/test_triage_tool.py

import unittest
from langchain_ai_agent.agents.tools.triage_tool import triage_chain
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class TestTriageTool(unittest.TestCase):
    def setUp(self):
        self.valid_ticket = {
            "text": (
                "Hi, I'm having trouble logging into my account. It says my password is incorrect "
                "but I'm sure it's right. Can someone help reset it urgently?"
            )
        }
        self.empty_ticket = {"text": ""}

    def test_output_structure_and_types(self):
        output = triage_chain.invoke(self.valid_ticket)

        self.assertIn("category", output)
        self.assertIn("urgency", output)
        self.assertIn("route_to", output)
        self.assertIn("explanation", output)

        self.assertIsInstance(output["category"], str)
        self.assertIsInstance(output["urgency"], str)
        self.assertIsInstance(output["route_to"], str)
        self.assertIsInstance(output["explanation"], str)

        logger.info(f"[Triage Output] {output}")

    def test_invalid_input_raises(self):
        with self.assertRaises(ValueError):
            triage_chain.invoke(self.empty_ticket)


if __name__ == "__main__":
    unittest.main()
