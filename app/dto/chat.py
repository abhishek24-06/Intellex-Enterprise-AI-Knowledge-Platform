from pydantic import BaseModel, Field

class ChatQueryRequest(BaseModel):
    query: str = Field(
        ...,
        min_length=1,
        description="Question to ask the Intellex knowledge base.",
    )

class ChatSource(BaseModel):
    document_id: int
    original_filename: str

class ChatQueryResponse(BaseModel):
    query: str
    answer: str
    sources: list[ChatSource]