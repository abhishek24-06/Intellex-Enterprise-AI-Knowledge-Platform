from __future__ import annotations

from dataclasses import dataclass
from typing import Any, TypedDict, Annotated
import operator

from sqlalchemy.orm import Session

from app.agents.critic_agent import CriticResult
from app.agents.tools.user_data_tools import DataAgentContext
from app.dto.rag_response import RAGResult
from app.models.users import User


class MultiAgentState(TypedDict, total=False):

    # User input

    original_query: str

    request_id: str

    # Agent 4 — Orchestrator

    route: str
    knowledge_query: str | None
    database_query: str | None
    route_reason: str | None

    # Agent 1 — Knowledge Agent

    retrieval_query: str | None
    rag_result: RAGResult | None

    # Agent 3 — Database Agent

    database_result: str | None
    # Agent 2 — Critic

    retry_target: str | None

    critique: CriticResult | None

    # Final response
    final_answer: str | None

    # Loop control
    attempt: int
    max_retries: int

    # Observability
    history: Annotated[
    list[dict[str, Any]],
    operator.add,
]

@dataclass
class MultiAgentContext:
    db: Session
    current_user: User