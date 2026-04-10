# agents/tools/kb_tool.py

import logging
import asyncio
from typing import Dict, List, Any
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import Runnable, RunnableLambda
from langchain_core.output_parsers import JsonOutputParser
from langchain_ai_agent.llm import get_llm

# Logger setup
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Prompt with few-shot examples
KB_PROMPT = PromptTemplate.from_template(
    """You are a helpful assistant converting documentation into a knowledge base.

Given the following document, create 3–5 helpful question-answer (Q&A) pairs.
Avoid vague or generic questions. Be specific and concise.

Example:

Q: What is the purpose of the onboarding guide?
A: It helps new users get started with our platform quickly.

Q: How can users reset their password?
A: Through 'Account Settings' > 'Security' > 'Reset Password'.

Now generate Q&A pairs for this document:

{text}

Return a JSON object:
{{
  "qa_pairs": [
    {{"question": "...", "answer": "..."}},
    ...
  ]
}}
"""
)

# DeepSeek chat model
llm = get_llm(temperature=0.3, max_tokens=1024)

async def _log_input(x: Dict[str, Any]) -> Dict[str, Any]:
    logger.info(f"[KB Tool] Generating Q&A for input length {len(x.get('text', ''))}")
    return x

# Output parser
parser = JsonOutputParser()

# Validation for structured output
async def _validate_qa_output(output: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(output, dict):
        raise ValueError("Output is not a valid dictionary.")
    if "qa_pairs" not in output or not isinstance(output["qa_pairs"], list):
        raise ValueError("Missing or invalid 'qa_pairs' key.")
    for qa in output["qa_pairs"]:
        if not isinstance(qa, dict) or "question" not in qa or "answer" not in qa:
            raise ValueError("Invalid QA pair structure.")
    return output

# Final Runnable chain
kb_writer_chain: Runnable = (
    {"text": lambda x: x["text"]}
    | RunnableLambda(_log_input)
    | KB_PROMPT
    | llm
    | parser
    | RunnableLambda(_validate_qa_output)
)
