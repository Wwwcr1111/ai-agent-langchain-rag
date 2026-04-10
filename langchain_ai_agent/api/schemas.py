# langchain_ai_agent/api/schemas.py

from pydantic import BaseModel, Field
from typing import Dict, Any, Optional


class AgentRequest(BaseModel):
    """Request schema for submitting a document chunk to the agent."""
    text: str = Field(..., min_length=5, description="Document chunk to be analyzed by the agent.")


class AgentResponse(BaseModel):
    """Response schema returned after agent processing."""
    task: Optional[str] = None
    output: Dict[str, Any]
    agent_trace: Optional[Dict[str, Any]] = None
