from __future__ import annotations

from datetime import UTC, datetime, timedelta

from sqlalchemy import select

from app.enums.enums import UserRole
from app.models.agent_execution import (
    AgentExecution,
)
from app.models.chat_session import (
    ChatSession,
)


def _build_scope_condition(
    *,
    current_user,
):
    """
    Organization admins are restricted to their
    organization.

    Super admins can observe all organizations.
    """

    if (
        current_user.role
        == UserRole.SUPER_ADMIN
    ):
        return None

    return (
        AgentExecution.organization_id
        == current_user.organization_id
    )


def get_chat_execution_trace(
    *,
    db,
    chat_id: int,
    current_user,
) -> list[AgentExecution]:

    conditions = [
        AgentExecution.chat_id == chat_id,
    ]

    scope_condition = (
        _build_scope_condition(
            current_user=current_user,
        )
    )

    if scope_condition is not None:
        conditions.append(
            scope_condition
        )

    stmt = (
        select(AgentExecution)
        .where(*conditions)
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


def get_observability_executions(
    *,
    db,
    current_user,
    window_hours: int,
) -> list[AgentExecution]:

    if window_hours <= 0:
        raise ValueError(
            "window_hours must be greater than zero."
        )

    cutoff = (
        datetime.now(UTC)
        - timedelta(
            hours=window_hours
        )
    )

    conditions = [
        AgentExecution.created_at >= cutoff,
    ]

    scope_condition = (
        _build_scope_condition(
            current_user=current_user,
        )
    )

    if scope_condition is not None:
        conditions.append(
            scope_condition
        )

    stmt = (
        select(AgentExecution)
        .where(*conditions)
        .order_by(
            AgentExecution.created_at.desc(),
            AgentExecution.execution_id.desc(),
        )
    )

    return list(
        db.execute(stmt)
        .scalars()
        .all()
    )