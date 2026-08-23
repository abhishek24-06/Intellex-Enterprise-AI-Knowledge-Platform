from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.agent_execution import AgentExecution


def get_chat_execution_trace(
    *,
    db: Session,
    chat_id: int,
) -> list[AgentExecution]:

    stmt = (
        select(AgentExecution)
        .where(
            AgentExecution.chat_id
            == chat_id
        )
        .order_by(
            AgentExecution.created_at.asc(),
            AgentExecution.execution_id.asc(),
        )
    )

    return list(
        db.execute(stmt)
        .scalars()
        .all()
    )