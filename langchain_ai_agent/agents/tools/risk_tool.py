# agents/tools/risk_tool.py

import logging, asyncio
from typing import Dict, Any, List
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import Runnable, RunnableLambda
from langchain_core.output_parsers import JsonOutputParser
from langchain_ai_agent.llm import get_llm

# Logger setup
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Prompt for identifying contract risk factors
RISK_PROMPT = PromptTemplate.from_template(
    """You are a legal assistant. Analyze the following contract text and identify any potential risk factors.

Focus on:
- Termination clauses
- Liability and indemnity
- Arbitration or jurisdiction
- Payment terms
- Unusual language

Return a JSON object:
- 'risks_found': a list of specific risks
- 'explanation': a high-level summary of why these risks were flagged

Contract Text:
{text}
"""
)

# DeepSeek chat model
llm = get_llm(temperature=0.3, max_tokens=1024)

async def _log_input(x: Dict[str, Any]) -> Dict[str, Any]:
    logger.info(f"[Risk Tool] Analyzing contract of length {len(x.get('text', ''))}")
    return x

# JSON output parser
parser = JsonOutputParser()

# Output validation function
async def _validate_risk_output(output: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(output, dict):
        raise ValueError("Output is not a valid dictionary.")
    if "risks_found" not in output or not isinstance(output["risks_found"], list):
        raise ValueError("Missing or invalid 'risks_found' key.")
    if "explanation" not in output or not isinstance(output["explanation"], str):
        raise ValueError("Missing or invalid 'explanation' key.")
    return output

# Final Runnable chain with logging and validation
risk_flagger_chain: Runnable = (
    {"text": lambda x: x["text"]}
    | RunnableLambda(_log_input)
    | RISK_PROMPT
    | llm
    | parser
    | RunnableLambda(_validate_risk_output)
)
