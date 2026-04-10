# langchain_ai_agent/agents/base_agent.py
import logging
from typing import Dict, Any, TypedDict, List
from langchain_core.runnables import Runnable, RunnableLambda
from langchain_core.prompts import PromptTemplate
from langchain_core.runnables import RunnableConfig
from langchain_core.output_parsers import StrOutputParser
from difflib import get_close_matches
import asyncio

# Tool imports (assume implemented as Runnables)
from langchain_ai_agent.agents.tools.summarize_tool import summarizer_chain
from langchain_ai_agent.agents.tools.risk_tool import risk_flagger_chain
from langchain_ai_agent.agents.tools.triage_tool import triage_chain
from langchain_ai_agent.agents.tools.kb_tool import kb_writer_chain
from langchain_ai_agent.llm import get_llm

# Setup logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Input schema (used for clarity and validation hints)
class AgentInput(TypedDict):
    text: str


# 1. Classification prompt
classification_prompt = PromptTemplate.from_template(
    """Given the following document content, classify it into one of the following labels:

- meeting_note
- contract
- support_ticket
- knowledge_base

Respond **with exactly one label only** from the list above. Do not include explanations or punctuation.

Document:
{text}"""
)


llm = get_llm(temperature=0.3, max_tokens=256)

# 2. Routing map
def route_to_tool(classification: str) -> Runnable:
    tool_map = {
        "meeting_note": summarizer_chain,
        "contract": risk_flagger_chain,
        "support_ticket": triage_chain,
        "knowledge_base": kb_writer_chain,
    }
    return tool_map.get(
        classification.strip().lower(),
        RunnableLambda(lambda x: {"error": "Unknown classification result"})
    )

# 3. LCEL agent pipeline
def get_agent_pipeline() -> Runnable:
    classify_chain: Runnable = (
        {"text": lambda x: x['text']}
        | classification_prompt
        |llm
        | StrOutputParser()
    )

    async def route_executor(input: AgentInput, config: RunnableConfig = {}) -> Dict[str, Any]:
        if "text" not in input or not input["text"].strip():
            logger.error("[Agent] Missing or empty 'text' input.")
            return {
                "task": None,
                "output": {"error": "Input must contain non-empty 'text' field"},
                "agent_trace": {}
            }

        try:
            classification = await classify_chain.ainvoke(input, config=config)
            classification = classification.strip().lower().replace(".", "")
            logger.debug(f"[Agent] Raw model output: {classification}")
        except Exception as e:
            logger.exception("[Agent] Classification chain failed.")
            return {
                "task": None,
                "output": {"error": f"Classification failed: {str(e)}"},
                "agent_trace": {"stage": "classification"}
            }

        allowed_labels = {"meeting_note", "contract", "support_ticket", "knowledge_base"}

        if classification not in allowed_labels:
            close = get_close_matches(classification, allowed_labels, n=1, cutoff=0.8)
            if close:
                logger.warning(f"[Agent] Fuzzy matched '{classification}' → '{close[0]}'")
                classification = close[0]
            else:
                logger.warning(f"[Agent] Invalid classification: {classification}")
                return {
                    "task": classification,
                    "output": {"error": f"Unknown classification result: {classification}"},
                    "agent_trace": {
                        "input_preview": input["text"][:100],
                        "routed_tool": classification
                    }
                }
        try:
            tool = route_to_tool(classification)
            output = await tool.ainvoke(input, config=config)
            logger.info(f"[Agent] Tool '{classification}' executed successfully.")
        except Exception as e:
            logger.exception("[Agent] Tool execution failed.")
            output = {"error": f"Tool execution failed: {str(e)}"}

        return {
            "task": classification,
            "output": output,
            "agent_trace": {
                "input_preview": input["text"][:100],
                "routed_tool": classification
            }
        }

    return RunnableLambda(route_executor)
