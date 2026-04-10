# tests/test_chat_agent.py

import unittest
import shutil
from pathlib import Path
from langchain_core.documents import Document
from langchain_ai_agent.agents.chat_agent import (
    get_chat_agent_with_memory,
    _build_citation_context,
    _resolve_citations,
)
from dotenv import load_dotenv
import asyncio

load_dotenv()


class TestChatAgent(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path("tests/tmp_chat_agent_store")
        self.test_dir.mkdir(parents=True, exist_ok=True)
        self.persist_dir = str(self.test_dir)
        self.agent = get_chat_agent_with_memory(persist_dir=self.persist_dir)

    def tearDown(self):
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_chat_agent_returns_answer(self):
        result = asyncio.run(
            self.agent.ainvoke({"question": "What is LangChain?"})
        )
        self.assertIn("graph_output", result)
        self.assertIsInstance(result["graph_output"], str)
        self.assertGreater(len(result["graph_output"]), 0)

    def test_chat_agent_handles_empty_question(self):
        result = asyncio.run(
            self.agent.ainvoke({"question": ""})
        )
        self.assertEqual(result["graph_output"], "[call_model] Empty or missing question.")

    def test_chat_agent_message_format(self):
        result = asyncio.run(
            self.agent.ainvoke({"question": "Tell me about vector search."})
        )
        self.assertIn("messages", result)
        self.assertIsInstance(result["messages"], list)
        self.assertTrue(any("vector" in msg.content.lower() for msg in result["messages"] if hasattr(msg, "content")))

    def test_build_citation_context_groups_chunks_by_filename(self):
        docs = [
            Document(page_content="alpha", metadata={"filename": "a.md"}),
            Document(page_content="beta", metadata={"filename": "a.md"}),
            Document(page_content="gamma", metadata={"filename": "b.md"}),
        ]

        context_text, source_map = _build_citation_context(docs)

        self.assertEqual(source_map, {"S1": "a.md", "S2": "b.md"})
        self.assertIn("[S1] a.md", context_text)
        self.assertIn("Chunk 1:\nalpha", context_text)
        self.assertIn("Chunk 2:\nbeta", context_text)
        self.assertIn("[S2] b.md", context_text)

    def test_resolve_citations_filters_unknown_and_deduplicates(self):
        resolved = _resolve_citations(["S2", "S2", "S99", "S1"], {"S1": "a.md", "S2": "b.md"})
        self.assertEqual(resolved, ["b.md", "a.md"])


if __name__ == "__main__":
    unittest.main()
