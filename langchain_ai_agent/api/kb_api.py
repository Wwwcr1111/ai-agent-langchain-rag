from fastapi import APIRouter, HTTPException, Query

from langchain_ai_agent.ingestion.reader import DocumentIngestor
from langchain_ai_agent.retriever.vector_store import DocumentEmbedder


router = APIRouter()


def _get_default_embedder() -> DocumentEmbedder:
    return DocumentEmbedder(persist_dir="faiss_index/default")


@router.get("/api/kb/documents")
async def list_kb_documents():
    embedder = _get_default_embedder()
    return {"documents": embedder.list_documents()}


@router.delete("/api/kb/documents/{filename}")
async def delete_kb_document(filename: str, doc_path: str = Query(...)):
    embedder = _get_default_embedder()
    ingestor = DocumentIngestor()
    try:
        return embedder.delete_document(filename=filename, doc_path=doc_path, ingestor=ingestor)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.post("/api/kb/rebuild")
async def rebuild_kb():
    embedder = _get_default_embedder()
    ingestor = DocumentIngestor()
    try:
        return embedder.rebuild_from_documents(ingestor)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
