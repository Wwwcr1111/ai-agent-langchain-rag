import logging
from typing import Dict, List, Any
from collections import defaultdict
import asyncio


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

semaphore = asyncio.Semaphore(5)

async def safe_invoke(agent, input: Dict[str, str]) -> Dict[str, Any]:
    async with semaphore:
        return await agent.ainvoke(input)


async def run_pipeline(source_path: str) -> Dict:
    logger.info("[Pipeline] Starting document ingestion...")

    from langchain_ai_agent.ingestion.reader import ingest_and_chunk
    from langchain_ai_agent.retriever.vector_store import DocumentEmbedder
    from langchain_ai_agent.agents.base_agent import get_agent_pipeline

    chunks = ingest_and_chunk(source_path)
    if not chunks:
        logger.warning("[Pipeline] No chunks found.")
        return {"status": "no_chunks"}

    async def format_chunk(i: int, chunk):
        if isinstance(chunk, dict):
            return chunk
        elif isinstance(chunk, str):
            return {
                "chunk_id": i,
                "text": chunk,
                "filename": "unknown.txt",
                "source_type": "raw",
                "doc_path": source_path
            }

    results = [
        format_chunk(i, chunk)
        for i, chunk in enumerate(chunks)
    ]

    formatted_chunks = await asyncio.gather(*results)

    # Embed the chunks
    embedder = DocumentEmbedder()
    embedder.build_or_update_index(formatted_chunks)

    # Document-level classification
    agent = get_agent_pipeline()
    doc_groups = defaultdict(list)

    for chunk in formatted_chunks:
        doc_groups[chunk["filename"]].append(chunk["text"])

    async def classify_doc(filename: str, chunks: List[str], agent):
        full_text = "\n".join(chunks)
        try:
            result = await safe_invoke(agent, {"text":full_text})
            return {
                "filename": filename,
                "label": str(result.get("task") or "unknown"),
                "output": result.get("output")
            }
        except Exception as e:
            logger.warning(f"[Pipeline] Failed to classify {filename}: {e}")
            return {"filename": filename, "label": "error", "output": {}}

    tasks = [
        classify_doc(filename, chunks, agent)
        for filename, chunks in doc_groups.items()
    ]

    doc_classification = await asyncio.gather(*tasks)

    return {
        "status": "classified",
        "documents": doc_classification
    }
