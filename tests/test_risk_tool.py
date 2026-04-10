# tests/test_risk_tool.py

import unittest
from langchain_ai_agent.agents.tools.risk_tool import risk_flagger_chain
from dotenv import load_dotenv
import logging

load_dotenv()
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class TestRiskTool(unittest.TestCase):
    def setUp(self):
        self.valid_contract = {
            "text": (
                "This agreement may be terminated by either party with 15 days' notice. "
                "Liability is limited to the amount paid in the last billing cycle. "
                "Disputes shall be resolved by binding arbitration in the State of Delaware."
            )
        }

        self.empty_contract = {"text": ""}

    def test_risk_output_structure_valid_input(self):
        output = risk_flagger_chain.invoke(self.valid_contract)

        self.assertIn("risks_found", output)
        self.assertIn("explanation", output)
        self.assertIsInstance(output["risks_found"], list)
        self.assertIsInstance(output["explanation"], str)

        logger.info(f"[Test Output] {output}")
        self.assertGreaterEqual(len(output["risks_found"]), 1)

    def test_risk_output_structure_invalid_input(self):
        with self.assertRaises(ValueError):
            risk_flagger_chain.invoke(self.empty_contract)


if __name__ == "__main__":
    unittest.main()
