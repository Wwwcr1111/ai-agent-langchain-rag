from fastapi import APIRouter, Query, HTTPException
from langchain_ai_agent.ingestion.reader import DocumentIngestor
from langchain_ai_agent.retriever.vector_store import DocumentEmbedder
from pathlib import Path

router = APIRouter()

@router.post("/run-ingestion-pipeline")
def run_ingestion_pipeline(
    path: str = Query(..., description="Directory path to ingest from"),
    namespace: str = Query("default", description="Namespace for FAISS storage")
):
    try:
        ingestor = DocumentIngestor()
        folder_path = Path(path)
        chunks = []
        for file_path in folder_path.glob("**/*"):
            if file_path.is_file():
                chunks.extend(ingestor.process_file(file_path))

        if not chunks:
            return {"status": "skipped", "reason": "No supported files found."}

        embedder = DocumentEmbedder(persist_dir=f"faiss_index/{namespace}")
        embedder.build_or_update_index(chunks)

        return {
            "status": "success",
            "num_chunks": len(chunks),
            "namespace": namespace
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
