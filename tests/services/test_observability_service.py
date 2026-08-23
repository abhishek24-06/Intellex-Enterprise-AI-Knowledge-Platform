from datetime import UTC, datetime
from types import SimpleNamespace

import pytest

from app.enums.enums import UserRole

from app.services.observability import (
    observability_service,
)


def make_execution(
    *,
    agent_name="knowledge_agent",
    route="KNOWLEDGE",
    attempt=0,
    status="SUCCESS",
    latency_ms=100.0,
    details=None,
):

    return SimpleNamespace(
        execution_id=1,
        chat_id=10,
        session_id=5,
        user_id=9,
        organization_id=2,
        request_id="req-1",
        agent_name=agent_name,
        route=route,
        attempt=attempt,
        status=status,
        latency_ms=latency_ms,
        details=details or {},
        created_at=datetime.now(UTC),
    )


def make_user(
    *,
    role=UserRole.ORG_ADMIN,
    organization_id=2,
):

    return SimpleNamespace(
        user_id=9,
        organization_id=organization_id,
        role=role,
    )


def test_summary_calculates_latency_and_retries(
    monkeypatch,
):

    rows = [
        make_execution(
            agent_name="orchestrator",
            latency_ms=100,
        ),
        make_execution(
            agent_name="knowledge_agent",
            latency_ms=300,
        ),
        make_execution(
            agent_name="knowledge_agent",
            latency_ms=500,
            attempt=1,
        ),
    ]

    monkeypatch.setattr(
        observability_service,
        "get_observability_executions",
        lambda **kwargs: rows,
    )

    result = (
        observability_service
        .build_observability_summary(
            db=None,
            current_user=make_user(),
            window_hours=24,
        )
    )

    assert result.total_executions == 3

    assert (
        result.successful_executions
        == 3
    )

    assert (
        result.failed_executions
        == 0
    )

    assert (
        result.average_latency_ms
        == 300
    )

    assert result.retry_count == 1

    assert result.retry_rate == pytest.approx(
    1 / 3,
    abs=0.00005,
)


def test_summary_calculates_critic_acceptance(
    monkeypatch,
):

    rows = [
        make_execution(
            agent_name="multi_agent_critic",
            details={
                "decision": "ACCEPT",
            },
        ),
        make_execution(
            agent_name="multi_agent_critic",
            details={
                "decision": "RETRY",
            },
        ),
        make_execution(
            agent_name="multi_agent_critic",
            details={
                "decision": "ACCEPT",
            },
        ),
    ]

    monkeypatch.setattr(
        observability_service,
        "get_observability_executions",
        lambda **kwargs: rows,
    )

    result = (
        observability_service
        .build_observability_summary(
            db=None,
            current_user=make_user(),
            window_hours=24,
        )
    )

    assert (
        result.critic_accept_count
        == 2
    )

    assert (
        result.critic_retry_count
        == 1
    )

    assert (
    result.critic_acceptance_rate
    == pytest.approx(
        2 / 3,
        abs=0.00005,
    )
)


def test_summary_groups_agent_latency(
    monkeypatch,
):

    rows = [
        make_execution(
            agent_name="knowledge_agent",
            latency_ms=100,
        ),
        make_execution(
            agent_name="knowledge_agent",
            latency_ms=300,
        ),
        make_execution(
            agent_name="database_agent",
            latency_ms=200,
        ),
    ]

    monkeypatch.setattr(
        observability_service,
        "get_observability_executions",
        lambda **kwargs: rows,
    )

    result = (
        observability_service
        .build_observability_summary(
            db=None,
            current_user=make_user(),
            window_hours=24,
        )
    )

    knowledge = next(
        item
        for item in result.agent_latency
        if item.agent_name
        == "knowledge_agent"
    )

    assert (
        knowledge.execution_count
        == 2
    )

    assert (
        knowledge.average_latency_ms
        == 200
    )

    assert (
        knowledge.min_latency_ms
        == 100
    )

    assert (
        knowledge.max_latency_ms
        == 300
    )