from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class AgentExecution(Base):
    __tablename__ = "agent_execution"

    execution_id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    chat_id: Mapped[int] = mapped_column(
        ForeignKey(
            "chat_history.chat_id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    session_id: Mapped[int] = mapped_column(
        ForeignKey(
            "chat_session.session_id",
            ondelete="CASCADE",
        ),
        nullable=False,
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey(
            "users.user_id",
        ),
        nullable=False,
    )

    organization_id: Mapped[int] = mapped_column(
        ForeignKey(
            "organizations.organization_id",
        ),
        nullable=False,
    )

    request_id: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        index=True,
    )

    agent_name: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
    )

    route: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
    )

    attempt: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )

    latency_ms: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    details: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(UTC),
    )


Index(
    "ix_agent_execution_chat_id_created_at",
    AgentExecution.chat_id,
    AgentExecution.created_at,
)

Index(
    "ix_agent_execution_org_created_at",
    AgentExecution.organization_id,
    AgentExecution.created_at,
)