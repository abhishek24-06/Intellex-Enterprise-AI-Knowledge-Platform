from __future__ import annotations

from app.dto.agent_execution import (
    AgentExecutionEvent,
)

from app.models.agent_execution import (
    AgentExecution,
)


class AgentExecutionService:

    @staticmethod
    def persist(
        *,
        db,
        chat_id: int,
        session_id: int,
        user_id: int,
        organization_id: int,
        events: list[AgentExecutionEvent],
    ) -> list[AgentExecution]:

        rows: list[AgentExecution] = []

        for event in events:

            row = AgentExecution(
                chat_id=chat_id,
                session_id=session_id,
                user_id=user_id,
                organization_id=organization_id,
                request_id=event.request_id,
                agent_name=event.agent_name,
                route=event.route,
                attempt=event.attempt,
                status=event.status,
                latency_ms=event.latency_ms,
                details=event.details,
            )

            db.add(row)
            rows.append(row)

        return rows