# langchain_ai_agent/api/main.py
from typing import List
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from langchain_ai_agent.api.schemas import AgentRequest, AgentResponse
from langchain_ai_agent.agents.base_agent import get_agent_pipeline
from langchain_ai_agent.feedback_loop.memory_store import MemoryStore
from langchain_ai_agent.pipelines.doc_to_action_pipeline import run_pipeline
from dotenv import load_dotenv
import logging
import os, asyncio
from langchain_ai_agent.api import ingest_api, kb_api, query_api, run_ingestion_pipeline

load_dotenv()

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

app = FastAPI(
    title="LangChain AI Agent API",
    description="API for processing documents with LangChain agent tools.",
    version="0.1.0"
)

app.include_router(ingest_api.router)
app.include_router(kb_api.router)
app.include_router(query_api.router)
app.include_router(run_ingestion_pipeline.router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent_pipeline = get_agent_pipeline()
memory_store = MemoryStore(persist_dir="memory_index")


# ========== 📄 Upload Single File ==========
@app.post("/upload-docs")
async def upload_docs(files: List[UploadFile] = File(...)):
    async def read_file(file: UploadFile):
        content = await file.read()
        try:
            text = content.decode("utf-8", errors="ignore")
        except Exception:
            text = "Could not decode file as plain text."
        return {"filename": file.filename, "extracted_text": text}     

    results = await asyncio.gather(*[read_file(file) for file in files])
    return {"uploaded": results}


# ========== 📂 Run Directory Pipeline ==========
class DirectoryPathRequest(BaseModel):
    path: str

@app.post("/run-pipeline")
async def run_directory_pipeline(payload: DirectoryPathRequest):
    path = payload.path

    logger.info(f"[PIPELINE] Running on path: {path}")

    if not os.path.isdir(path):
        raise HTTPException(status_code=400, detail="Provided path is not a valid directory")

    try:
        result = await run_pipeline(path)
        return result
    except Exception as e:
        logger.exception("[PIPELINE] Failed to run pipeline")
        raise HTTPException(status_code=500, detail=str(e))


# ========== 🤖 Agent ==========
@app.post("/run-agent", response_model=AgentResponse)
async def run_agent(request: AgentRequest):
    logger.info(f"[API] Received request with text length: {len(request.text)}")

    try:
        if not request.text or not request.text.strip():
            raise HTTPException(status_code=400, detail="Input must contain non-empty 'text' field")

        logger.info(f"🧠 Request.text = {request.text!r}")

        memory_examples = memory_store.query_similar(request.text, k=2)

        result = await agent_pipeline.ainvoke({"text": request.text})

        memory_store.add_experience(
            input_text=request.text,
            output=result["output"],
            task=result["task"],
            metadata={"source": "api"}
        )

        result["agent_trace"]["similar_cases"] = memory_examples # Need to later inject them into the LLM prompt

        return AgentResponse(**result)

    except Exception as e:
        logger.exception("[API] Agent failed to process input.")
        raise HTTPException(status_code=500, detail=str(e))
