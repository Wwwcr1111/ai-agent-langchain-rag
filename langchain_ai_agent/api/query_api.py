from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse
from langchain_ai_agent.agents.chat_agent import get_chat_agent_with_memory
from langgraph.store.memory import InMemoryStore
import traceback
import logging
import uuid
import json

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

router = APIRouter()

# Shared store instance (same as in chat_agent)
store = InMemoryStore()

@router.get("/api/query")
async def query_kb(
    question: str = Query(...),
    namespace: str = Query("default"),
    thread_id: str = Query(None),
    stream: bool = Query(False)
):
    try:
        thread_id = thread_id or str(uuid.uuid4())
        logger.info(f"[Thread] Using thread_id = {thread_id}")
        agent = get_chat_agent_with_memory(persist_dir=f"faiss_index/{namespace}")

        config = {"configurable": {"thread_id": thread_id}}
        payload = {"question": question, "messages": []}

        if stream:
            async def event_stream():
                async for update in agent.astream(payload, config=config, stream_mode="updates"):
                    yield f"data: {json.dumps(update)}\n\n"
            return StreamingResponse(event_stream(), media_type="text/event-stream")

        result = await agent.with_config(config).ainvoke(payload)
        answer = result.get("graph_output", "").strip()
        sources = result.get("sources", [])
        if not answer:
            raise HTTPException(status_code=500, detail="Agent returned no answer.")
        return JSONResponse(content={
            "results": [answer],
            "sources": sources,
            "thread_id": thread_id
        })

    except Exception as e:
        logger.error(f"Agent execution failed: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/state")
async def get_thread_state(thread_id: str = Query(...)):
    try:
        config = {"configurable": {"thread_id": thread_id}}
        agent = get_chat_agent_with_memory(persist_dir="faiss_index/default")
        state = await agent.get_state(config)
        return JSONResponse(content={"state": state.values})
    except Exception as e:
        logger.error(f"Failed to retrieve state: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch state")


@router.post("/api/reset")
async def reset_thread(thread_id: str = Query(...)):
    try:
        namespace = ("default", thread_id)
        keys = await store.list_namespaces(prefix=namespace)
        for ns in keys:
            await store.delete(ns, "state")  # assuming state is stored under key "state"
        return JSONResponse(content={"message": f"Thread {thread_id} state deleted."})
    except Exception as e:
        logger.error(f"Failed to reset thread: {e}")
        raise HTTPException(status_code=500, detail="Failed to reset thread")
