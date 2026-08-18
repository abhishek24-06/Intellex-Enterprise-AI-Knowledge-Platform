from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

class ChatHistorySource(BaseModel):

    document_id:int
    original_filename:str

class ChatHistoryMessageResponse(BaseModel):

    chat_id: int
    session_id: int
    question: str
    answer: str
    created_at: datetime
    feedback: str | None
    sources: list[ChatHistorySource]

class ChatHistoryListResponse(BaseModel):
    messages: list[ChatHistoryMessageResponse]

class ChatSessionUpdateRequest(BaseModel):
    title: str | None = None
    is_pinned: bool | None = None