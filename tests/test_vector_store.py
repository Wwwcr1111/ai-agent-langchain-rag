# tests/test_vector_store.py

import unittest
from pathlib import Path
import shutil
from langchain_ai_agent.retriever.vector_store import DocumentEmbedder
from dotenv import load_dotenv

load_dotenv()


class TestDocumentEmbedder(unittest.TestCase):
    def setUp(self):
        # Create a temporary FAISS index directory for testing
        self.test_index_path = Path("tests/test_faiss_index")
        self.embedder = DocumentEmbedder(persist_dir=str(self.test_index_path))

        self.sample_chunks = [
            {
                "chunk_id": 0,
                "text": "LangChain helps build LLM-powered apps using composable components.",
                "filename": "doc1.txt",
                "source_type": "txt",
                "doc_path": "/fake/path/doc1.txt"
            },
            {
                "chunk_id": 1,
                "text": "FAISS is a library for efficient similarity search and clustering of dense vectors.",
                "filename": "doc1.txt",
                "source_type": "txt",
                "doc_path": "/fake/path/doc1.txt"
            }
        ]
        self.sample_doc_path = Path("tests/doc1.txt")
        self.sample_doc_path.write_text("doc1 content", encoding="utf-8")

    class StubIngestor:
        def __init__(self, chunk_map):
            self.chunk_map = chunk_map

        def process_file(self, filepath):
            return self.chunk_map.get(str(filepath), [])

    def tearDown(self):
        # Clean up the test FAISS directory
        if self.test_index_path.exists():
            shutil.rmtree(self.test_index_path)
        if self.sample_doc_path.exists():
            self.sample_doc_path.unlink()

    def test_build_index_successfully(self):
        self.embedder.build_or_update_index(self.sample_chunks)
        retriever = self.embedder.get_retriever()
        self.assertIsNotNone(retriever)

        # Access internal FAISS index
        index = self.embedder._vector_store.index
        self.assertEqual(index.d, 384)
        self.assertEqual(index.ntotal, 2)

    def test_deduplication_skips_duplicates(self):
        self.embedder.build_or_update_index(self.sample_chunks)
        self.embedder.build_or_update_index(self.sample_chunks)  # Add same again
        retriever = self.embedder.get_retriever()
        results = retriever.get_relevant_documents("LangChain vector search")
        self.assertLessEqual(len(results), 2)

    def test_query_returns_documents(self):
        self.embedder.build_or_update_index(self.sample_chunks)
        results = self.embedder.query("How does LangChain work?")
        self.assertGreater(len(results), 0)
        self.assertIn("LangChain", results[0].page_content)

    def test_build_index_empty_input(self):
        with self.assertRaises(ValueError):
            self.embedder.build_or_update_index([])

    def test_schema_validation_raises(self):
        with self.assertRaises(Exception):
            self.embedder.build_or_update_index([{"text": "Missing metadata"}])

    def test_list_documents_groups_chunks(self):
        chunks = [
            {**self.sample_chunks[0], "doc_path": str(self.sample_doc_path)},
            {**self.sample_chunks[1], "doc_path": str(self.sample_doc_path)},
        ]
        self.embedder.build_or_update_index(chunks)

        documents = self.embedder.list_documents()
        self.assertEqual(len(documents), 1)
        self.assertEqual(documents[0]["filename"], "doc1.txt")
        self.assertEqual(documents[0]["chunk_count"], 2)
        self.assertFalse(documents[0]["missing"])

    def test_delete_document_rebuilds_remaining_index(self):
        other_doc_path = Path("tests/doc2.txt")
        other_doc_path.write_text("doc2 content", encoding="utf-8")
        try:
            chunks = [
                {**self.sample_chunks[0], "doc_path": str(self.sample_doc_path)},
                {
                    "chunk_id": 0,
                    "text": "Other document text",
                    "filename": "doc2.txt",
                    "source_type": "txt",
                    "doc_path": str(other_doc_path),
                },
            ]
            self.embedder.build_or_update_index(chunks)
            ingestor = self.StubIngestor(
                {
                    str(other_doc_path): [
                        {
                            "chunk_id": 0,
                            "text": "Other document text",
                            "filename": "doc2.txt",
                            "source_type": "txt",
                            "doc_path": str(other_doc_path),
                        }
                    ]
                }
            )

            result = self.embedder.delete_document("doc1.txt", str(self.sample_doc_path), ingestor)

            self.assertEqual(result["remaining_documents"], 1)
            documents = self.embedder.list_documents()
            self.assertEqual([item["filename"] for item in documents], ["doc2.txt"])
        finally:
            if other_doc_path.exists():
                other_doc_path.unlink()

    def test_rebuild_from_documents_skips_missing_files(self):
        self.embedder.register_documents(
            [
                {"filename": "doc1.txt", "source_type": "txt", "doc_path": str(self.sample_doc_path)},
                {"filename": "missing.txt", "source_type": "txt", "doc_path": "tests/missing.txt"},
            ]
        )
        ingestor = self.StubIngestor(
            {
                str(self.sample_doc_path): [
                    {
                        "chunk_id": 0,
                        "text": "doc1 content",
                        "filename": "doc1.txt",
                        "source_type": "txt",
                        "doc_path": str(self.sample_doc_path),
                    }
                ]
            }
        )

        result = self.embedder.rebuild_from_documents(ingestor)

        self.assertEqual(result["rebuilt_documents"], 1)
        self.assertEqual(len(result["skipped_files"]), 1)
        self.assertEqual(self.embedder.list_documents()[0]["filename"], "doc1.txt")


if __name__ == "__main__":
    unittest.main()
