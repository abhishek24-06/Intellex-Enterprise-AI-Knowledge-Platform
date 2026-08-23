from unittest.mock import Mock

from app.dto.agent_execution import (
    AgentExecutionEvent,
)
from evaluation.observability.agent_execution_service import AgentExecutionService



def test_agent_execution_events_are_persisted():

    db = Mock()

    events = [
        AgentExecutionEvent(
            request_id="req-123",
            agent_name="orchestrator",
            route="HYBRID",
            attempt=0,
            status="SUCCESS",
            latency_ms=120.5,
            details={
                "route": "HYBRID",
            },
        ),
        AgentExecutionEvent(
            request_id="req-123",
            agent_name="knowledge_agent",
            route="HYBRID",
            attempt=0,
            status="SUCCESS",
            latency_ms=850.2,
            details={
                "retrieved_chunks": 5,
                "retrieved_documents": 2,
            },
        ),
    ]

    rows = AgentExecutionService.persist(
        db=db,
        chat_id=100,
        session_id=10,
        user_id=9,
        organization_id=2,
        events=events,
    )

    assert len(rows) == 2

    first = rows[0]

    assert first.chat_id == 100
    assert first.session_id == 10
    assert first.user_id == 9
    assert first.organization_id == 2

    assert first.request_id == "req-123"
    assert first.agent_name == "orchestrator"
    assert first.route == "HYBRID"
    assert first.status == "SUCCESS"
    assert first.latency_ms == 120.5

    second = rows[1]

    assert second.agent_name == (
        "knowledge_agent"
    )

    assert second.details[
        "retrieved_chunks"
    ] == 5

    assert db.add.call_count == 2