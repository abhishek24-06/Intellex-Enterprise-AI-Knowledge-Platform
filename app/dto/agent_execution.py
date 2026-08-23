from __future__ import annotations

from pydantic import BaseModel, Field


class AgentExecutionEvent(BaseModel):
    request_id: str
    agent_name: str

    route: str | None = None

    attempt: int = 0

    status: str

    latency_ms: float

    details: dict = Field(
        default_factory=dict,
    )