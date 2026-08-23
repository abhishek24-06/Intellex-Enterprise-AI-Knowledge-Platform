from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class AgentExecutionResponse(BaseModel):
    execution_id: int

    chat_id: int
    session_id: int

    user_id: int
    organization_id: int

    request_id: str

    agent_name: str

    route: str | None = None

    attempt: int

    status: str

    latency_ms: float

    details: dict = Field(
        default_factory=dict,
    )

    created_at: datetime


class AgentLatencySummary(BaseModel):
    agent_name: str

    execution_count: int

    average_latency_ms: float

    min_latency_ms: float

    max_latency_ms: float


class RouteSummary(BaseModel):
    route: str

    execution_count: int


class ObservabilitySummaryResponse(BaseModel):
    window_hours: int

    total_executions: int

    successful_executions: int

    failed_executions: int

    average_latency_ms: float

    retry_count: int

    retry_rate: float

    critic_accept_count: int

    critic_retry_count: int

    critic_acceptance_rate: float

    agent_latency: list[
        AgentLatencySummary
    ]

    routes: list[
        RouteSummary
    ]


class ChatExecutionTraceResponse(BaseModel):
    chat_id: int

    execution_count: int

    executions: list[
        AgentExecutionResponse
    ]