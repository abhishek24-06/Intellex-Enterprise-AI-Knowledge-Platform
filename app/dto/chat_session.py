from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, Field, field_validator,ConfigDict

class ChatSessionCreateRequest(BaseModel):

    title: str | None = Field(default=None,max_length=255)

    @field_validator("title")
    @classmethod
    def validate_title(cls,value: str | None) -> str | None:

        if value is None:
            return None

        value = value.strip()

        if not value:
            return None

        return value

class ChatSessionResponse(BaseModel):

    model_config = ConfigDict(
        from_attributes=True,
    )

    session_id: int
    title: str | None
    created_at: datetime
    last_active: datetime
    is_pinned: bool

class ChatSessionListResponse(BaseModel):

    model_config = ConfigDict(
        from_attributes=True,
    )
    
    sessions: list[ChatSessionResponse]