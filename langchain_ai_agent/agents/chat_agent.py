from langchain.chains import create_history_aware_retriever
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder, PromptTemplate
from langchain_ai_agent.retriever.vector_store import DocumentEmbedder
from langchain_core.documents import Document
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, RemoveMessage
from langgraph.graph import StateGraph, END, MessagesState
from langgraph.checkpoint.memory import MemorySaver
from typing import Literal, Any
import logging
import json

from pydantic import BaseModel, Field, ValidationError

from langchain_ai_agent.llm import get_llm

# Configure logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Shared persistent memory store
store = MemorySaver()

# Use MessagesState for built-in message memory support
class AgentState(MessagesState):
    summary: str | None = None
    question: str
    graph_output: str | None = None
    sources: list[str] | None = None


class CitationAnswer(BaseModel):
    answer: str = Field(default="")
    citations: list[str] = Field(default_factory=list)


def create_prompt():
    system_instruction = """Given a chat history and the latest user question \
        which might reference context in the chat history, formulate a standalone question \
        which can be understood without the chat history. Do NOT answer the question, \
        just reformulate it if needed and otherwise return it as is."""

    return ChatPromptTemplate.from_messages([
        ("system", system_instruction),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}")
    ])

def create_doc_chains_prompt():
    return PromptTemplate(
        template="""You are an assistant for question-answering tasks.
Use only the provided context to answer the question.
Each source is labeled like [S1], [S2].

Rules:
1. Return valid JSON only.
2. "answer" must contain the final answer text.
3. "citations" must contain only source labels you actually used, like ["S1", "S2"].
4. Do not include any source label that was not needed for the answer.
5. If the answer cannot be supported by the context, say you do not know and return an empty citations list.

Context:
{context}

Question:
{input}

JSON:
{{
  "answer": "...",
  "citations": ["S1"]
}}""",
        input_variables=["context", "input"],
    )


def _normalize_source_name(doc: Document) -> str | None:
    metadata = getattr(doc, "metadata", {}) or {}
    return metadata.get("filename") or metadata.get("doc_path")


def _build_citation_context(docs: list[Document]) -> tuple[str, dict[str, str]]:
    source_map: dict[str, str] = {}
    grouped_chunks: dict[str, list[str]] = {}

    for doc in docs:
        source_name = _normalize_source_name(doc)
        if not source_name:
            continue

        label = next((key for key, value in source_map.items() if value == source_name), None)
        if label is None:
            label = f"S{len(source_map) + 1}"
            source_map[label] = source_name
            grouped_chunks[label] = []

        content = (doc.page_content or "").strip()
        if content:
            grouped_chunks[label].append(content)

    sections: list[str] = []
    for label, source_name in source_map.items():
        chunks = grouped_chunks.get(label, [])
        if not chunks:
            continue
        chunk_blocks = "\n\n".join(
            f"Chunk {index + 1}:\n{chunk}"
            for index, chunk in enumerate(chunks)
        )
        sections.append(f"[{label}] {source_name}\n{chunk_blocks}")

    return "\n\n".join(sections), source_map


def _extract_message_text(response: Any) -> str:
    content = getattr(response, "content", response)
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        return "".join(
            item.get("text", "") if isinstance(item, dict) else str(item)
            for item in content
        ).strip()
    return str(content).strip()


def _parse_citation_answer(raw_text: str) -> CitationAnswer:
    try:
        return CitationAnswer.model_validate_json(raw_text)
    except ValidationError:
        logger.warning("[Citations] Structured parse failed, falling back to raw answer.")
        return CitationAnswer(answer=raw_text, citations=[])
    except json.JSONDecodeError:
        logger.warning("[Citations] JSON decode failed, falling back to raw answer.")
        return CitationAnswer(answer=raw_text, citations=[])


def _resolve_citations(citation_labels: list[str], source_map: dict[str, str]) -> list[str]:
    resolved_sources: list[str] = []
    for label in citation_labels:
        source_name = source_map.get(label.strip())
        if source_name and source_name not in resolved_sources:
            resolved_sources.append(source_name)
    return resolved_sources

def get_chat_agent_with_memory(persist_dir: str):
    embedder = DocumentEmbedder(persist_dir=persist_dir)
    retriever = embedder.get_retriever(k=10)

    llm = get_llm(temperature=0.3, max_tokens=1024)

    contextualize_q_prompt = create_prompt()
    try:
        history_aware_retriever = create_history_aware_retriever(
            llm, retriever, contextualize_q_prompt
        )
    except Exception as e:
        logger.info(f"[Retriever] {e}")
        history_aware_retriever = retriever

    stuff_prompt = create_doc_chains_prompt()

    workflow = StateGraph(AgentState)

    def call_model(state: AgentState) -> dict:
        logger.info(f"[call_model] Full state: {state}")
        question = state.get("question", "")
        summary = state.get("summary", "")

        if not question:
            return {
                "messages": [AIMessage(content="[call_model] Empty or missing question.")],
                "graph_output": "[call_model] Empty or missing question."
            }

        system_messages = [SystemMessage(content=f"Summary of conversation earlier: {summary}")]
        chat_history = system_messages + state["messages"] if summary else state["messages"]

        logger.info(f"We have this information {chat_history}")

        chain_input = {
            "input": question,
            "chat_history": chat_history
        }

        logger.info(f"[call_model] chain_input: {chain_input}")
        retrieved_docs = history_aware_retriever.invoke(chain_input)
        context_text, source_map = _build_citation_context(retrieved_docs)

        if not context_text:
            answer_text = "I don't know."
            sources = []
        else:
            prompt_text = stuff_prompt.format(context=context_text, input=question)
            raw_response = llm.invoke(prompt_text)
            parsed_response = _parse_citation_answer(_extract_message_text(raw_response))
            answer_text = parsed_response.answer.strip() or "I don't know."
            sources = _resolve_citations(parsed_response.citations, source_map)

        updated_messages = state.get("messages", []) + [
            HumanMessage(content=question),
            AIMessage(content=answer_text)
        ]

        return {
            "messages": updated_messages,
            "graph_output": answer_text,
            "sources": sources,
        }

    def should_continue(state: AgentState) -> Literal["summarize_conversation", END]:
        if len(state.get("messages", [])) > 6:
            return "summarize_conversation"
        return END

    def summarize_conversation(state: AgentState) -> dict:
        summary = state.get("summary", "")
        prompt = (
            f"This is summary of the conversation to date: {summary}\n\n"
            "Extend the summary by taking into account the new messages above:"
            if summary
            else "Create a summary of the conversation above:"
        )
        messages = state["messages"] + [HumanMessage(content=prompt)]
        response = llm.invoke(messages)
        delete_messages = [RemoveMessage(id=m.id) for m in state["messages"][:-2]]

        return {
            "summary": response.content,
            "messages": delete_messages
        }

    # Build the graph
    workflow.add_node("conversation", call_model)
    workflow.add_node("summarize_conversation", summarize_conversation)
    workflow.set_entry_point("conversation")
    workflow.add_conditional_edges("conversation", should_continue)
    workflow.add_edge("summarize_conversation", END)

    workflow = workflow.compile(checkpointer=store)
    logger.info("[LangGraph] Compiled with MemorySaver store")
    return workflow
