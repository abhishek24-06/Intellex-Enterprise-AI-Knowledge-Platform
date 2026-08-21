from pydantic import BaseModel, Field

from app.dto.retrieved_chunk import RetrievedChunk


class MultiAgentResponse(BaseModel):
    query: str
    answer: str
    sources: list[RetrievedChunk] = Field(
        default_factory=list
    )