# agents/tools/summarize_tool.py

import logging
from typing import Dict, Any
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import Runnable, RunnableLambda
from langchain_core.output_parsers import JsonOutputParser
from langchain_ai_agent.llm import get_llm

# Logger setup
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Prompt Template for meeting summarization
SUMMARIZE_PROMPT = PromptTemplate.from_template(
    """You are a helpful assistant. Summarize the following meeting note into a concise paragraph and bullet points.

Document:
{text}

Return a JSON object:
- 'summary': the overall summary (3–5 sentences)
- 'bullet_points': a list of key discussion points
"""
)

# DeepSeek chat model
llm = get_llm(temperature=0.3, max_tokens=1024)

async def _log_input(x: Dict[str, Any]) -> Dict[str, Any]:
    logger.info(f"[Summarizer] Summarizing text of length {len(x.get('text', ''))}")
    return x

# Output parser for structured JSON
parser = JsonOutputParser()

# Validation for summarization output format
async def _validate_summary_output(output: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(output, dict):
        raise ValueError("Output is not a valid dictionary.")
    if "summary" not in output or not isinstance(output["summary"], str):
        raise ValueError("Missing or invalid 'summary' key.")
    if "bullet_points" not in output or not isinstance(output["bullet_points"], list):
        raise ValueError("Missing or invalid 'bullet_points' key.")
    return output

# Final Runnable chain with logging and validation
summarizer_chain: Runnable = (
    {"text": lambda x: x["text"]}
    | RunnableLambda(_log_input)
    | SUMMARIZE_PROMPT
    | llm
    | parser
    | RunnableLambda(_validate_summary_output)
)
