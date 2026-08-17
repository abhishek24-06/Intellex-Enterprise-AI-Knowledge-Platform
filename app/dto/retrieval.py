from pydantic import BaseModel, Field, field_validator


class RetrievalRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=1,
        description="Natural-language search query.",
    )

    @field_validator("query")
    @classmethod
    def validate_query(cls, value: str) -> str:
        value = value.strip()

        if not value:
            raise ValueError("Query cannot be empty or whitespace.")

        return value

class RetrievedChunkResponse(BaseModel):

    document_id: int
    chunk_id: int
    chunk_index: int
    chunk_text: str
    token_count: int
    metadata: dict
    vector_score: float
    rerank_score: float | None


class RetrievalResponse(BaseModel):

    query: str
    results: list[RetrievedChunkResponse]