from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class AgenticEvaluationRecord(BaseModel):
    id: str
    category: str

    user_input: str
    reference: str

    response: str

    route: str | None = None

    retrieved_contexts: list[str] = Field(
        default_factory=list
    )

    database_evidence: str | None = None

    source_count: int = 0

    sources: list[dict[str, Any]] = Field(
        default_factory=list
    )