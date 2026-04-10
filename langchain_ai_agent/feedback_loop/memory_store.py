# langchain_ai_agent/feedback_loop/memory_store.py
'''
Recall similar past inputs (document chunks)

Reuse past outputs as experience

Enable future tools (like routing or generation) to learn from prior decisions
'''

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional

from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.docstore.document import Document
from pydantic import BaseModel, ValidationError

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


class ExperienceRecord(BaseModel):
    """
    Schema for each experience stored in memory:
    - input_text: original document chunk
    - task: tool type or classification (e.g., summarizer, risk)
    - output: structured result from agent
    - meta: optional extra info (e.g., filename, chunk_id)
    """
    input_text: str
    task: str
    output: Dict
    meta: Optional[Dict] = None


class MemoryStore:
    """
    Long-term memory store that logs agent experiences and enables similarity-based recall.
    Backed by FAISS and HuggingFace embeddings.
    """

    def __init__(
        self,
        persist_dir: str = "memory_index",
        embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    ):
        """
        Initialize the memory store.

        Args:
            persist_dir (str): Directory to store FAISS index and logs
            embedding_model (str): Name of sentence-transformer model to use
        """
        self.persist_dir = Path(persist_dir)
        self.metadata_log = self.persist_dir / "memory_log.jsonl"
        self.embeddings = HuggingFaceEmbeddings(model_name=embedding_model)

        if self.persist_dir.exists():
            try:
                self.vector_store = FAISS.load_local(
                    folder_path=str(self.persist_dir),
                    embeddings=self.embeddings
                )
                logger.info("[MemoryStore] Loaded existing FAISS index from disk.")
            except Exception as e:
                logger.error(f"[MemoryStore] Failed to load FAISS index: {e}")
                self.vector_store = None
        else:
            self.persist_dir.mkdir(parents=True, exist_ok=True)
            self.vector_store = None
            logger.info("[MemoryStore] Initialized new FAISS memory store.")

    def add_experience(
        self,
        input_text: str,
        output: Dict,
        task: str,
        metadata: Optional[Dict] = None
    ) -> None:
        """
        Log an agent experience into memory.

        Args:
            input_text (str): Document chunk
            output (Dict): Output from the agent
            task (str): Task type (e.g., "summarization", "triage")
            metadata (Optional[Dict]): Extra info like filename, chunk_id
        """
        try:
            record = ExperienceRecord(
                input_text=input_text,
                task=task,
                output=output,
                meta=metadata or {}
            )
        except ValidationError as e:
            logger.error(f"[MemoryStore] Experience validation failed: {e}")
            return

        # Add to vector DB
        doc = Document(page_content=record.input_text, metadata={
            "task": record.task,
            **(record.meta or {}),
            "output": record.output  # Optional: remove if too large
        })

        try:
            if self.vector_store:
                self.vector_store.add_documents([doc])
            else:
                self.vector_store = FAISS.from_documents([doc], self.embeddings)
            self.vector_store.save_local(str(self.persist_dir))
            logger.info(f"[MemoryStore] Experience added and persisted for task '{task}'.")
        except Exception as e:
            logger.error(f"[MemoryStore] Failed to update vector store: {e}")

        # Append to memory log
        try:
            with open(self.metadata_log, "a") as f:
                f.write(record.model_dump_json() + "\n")
        except Exception as e:
            logger.error(f"[MemoryStore] Failed to write log: {e}")

    def query_similar(self, input_text: str, k: int = 3) -> List[Dict]:
        """
        Retrieve similar past experiences based on input text.

        Args:
            input_text (str): The new chunk to compare
            k (int): Number of most similar examples to return

        Returns:
            List[Dict]: Past experiences with metadata
        """
        if not self.vector_store:
            logger.warning("[MemoryStore] No vector store loaded.")
            return []

        try:
            results = self.vector_store.similarity_search(input_text, k=k)
            logger.info(f"[MemoryStore] Found {len(results)} similar experiences.")
            return [
                {
                    "text": doc.page_content,
                    "metadata": doc.metadata
                }
                for doc in results
            ]
        except Exception as e:
            logger.error(f"[MemoryStore] Similarity search failed: {e}")
            return []
