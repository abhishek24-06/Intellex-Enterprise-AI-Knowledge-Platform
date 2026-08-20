from __future__ import annotations
from typing import Any, TypedDict
from dataclasses import dataclass
from sqlalchemy.orm import Session

from app.agents.critic_agent import CriticResult
from app.dto.rag_response import RAGResult
from app.models.users import User

class RAGAgentState(TypedDict,total=False):

    original_query: str
    retrieval_query: str
    attempt: int
    max_retries: int
    rag_result: RAGResult | None
    critique: CriticResult | None
    final_answer: str | None
    history: list[dict[str, Any]]

@dataclass
class RAGGraphContext:
    db: Session
    current_user: User
    