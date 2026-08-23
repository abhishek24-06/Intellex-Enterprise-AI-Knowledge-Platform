from pydantic import BaseModel, Field

from app.dto.agent_execution import AgentExecutionEvent
from app.dto.retrieved_chunk import RetrievedChunk


class MultiAgentResponse(BaseModel):
    query: str
    answer: str
    sources: list[RetrievedChunk] = Field(
        default_factory=list
    )

    execution_trace: list[
        AgentExecutionEvent
    ] = Field(
        default_factory=list,
        exclude=True,
        repr=False,
    )