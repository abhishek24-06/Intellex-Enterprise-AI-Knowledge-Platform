from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app.agents.critic_agent import (
    CriticDecision,
    CriticResult,
    RetryTarget,
)
from app.agents.graph.graph import (
    build_multi_agent_graph,
)
from app.agents.multi_agent_state import (
    MultiAgentContext,
)
from app.agents.orchestrator_agent import (
    AgentRoute,
    OrchestratorDecision,
)
from app.dto.rag_response import RAGResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_user(
    *,
    user_id: int = 1,
    organization_id: int = 1,
):
    return SimpleNamespace(
        user_id=user_id,
        organization_id=organization_id,
    )


def make_chunk(
    *,
    document_id: int = 35,
    original_filename: str = (
        "02_organization_it_operations.pdf"
    ),
    chunk_text: str = (
        "Operators should check service health, "
        "recent deployments, active incidents, "
        "and monitoring state before changing a service."
    ),
):
    return SimpleNamespace(
        document_id=document_id,
        original_filename=original_filename,
        chunk_text=chunk_text,
        chunk_id=1,
        chunk_index=0,
        token_count=30,
    )


def make_rag_result(
    *,
    query: str,
    answer: str,
    sources=None,
):
    return RAGResult(
        query=query,
        answer=answer,
        sources=sources or [],
    )


def make_context():
    return MultiAgentContext(
        db=Mock(name="db"),
        current_user=make_user(
            user_id=7,
            organization_id=2,
        ),
    )


def make_orchestrator(
    *,
    route: AgentRoute,
    knowledge_query: str | None = None,
    database_query: str | None = None,
    reason: str = "Test route.",
):
    orchestrator = Mock()

    orchestrator.route.return_value = (
        OrchestratorDecision(
            route=route,
            knowledge_query=knowledge_query,
            database_query=database_query,
            reason=reason,
        )
    )

    return orchestrator


def make_critic(
    *,
    decision: CriticDecision,
    retry_target: RetryTarget | None = None,
    improved_query: str | None = None,
    context_relevance: float = 0.95,
    faithfulness: float = 0.95,
    answer_correctness: float = 0.95,
    reason: str = "Answer is sufficiently grounded.",
):
    critic = Mock()

    critic.evaluate.return_value = (
        CriticResult(
            decision=decision,
            context_relevance=context_relevance,
            faithfulness=faithfulness,
            answer_correctness=answer_correctness,
            reason=reason,
            retry_target=retry_target,
            improved_query=improved_query,
        )
    )

    return critic


def build_graph(
    *,
    orchestrator,
    rag_service,
    data_agent,
    critic_agent,
    llm_client,
):
    return build_multi_agent_graph(
        orchestrator=orchestrator,
        rag_service=rag_service,
        data_agent=data_agent,
        critic_agent=critic_agent,
        llm_client=llm_client,
    )


def history_nodes(result):
    return {
        item["node"]
        for item in result.get(
            "history",
            [],
        )
        if isinstance(item, dict)
        and "node" in item
    }


# ===========================================================================
# 1. KNOWLEDGE ROUTE
# ===========================================================================


def test_knowledge_route_runs_knowledge_synthesis_and_critic():

    query = (
        "Explain why operational checks are important."
    )

    chunk = make_chunk()

    orchestrator = make_orchestrator(
        route=AgentRoute.KNOWLEDGE,
        knowledge_query=(
            "Why are service health, recent deployments, "
            "active incidents, and monitoring checks important?"
        ),
        reason=(
            "The query requires enterprise document knowledge."
        ),
    )

    rag_service = Mock()

    rag_service.answer.return_value = make_rag_result(
        query=(
            "Why are service health, recent deployments, "
            "active incidents, and monitoring checks important?"
        ),
        answer=(
            "These checks establish the current state "
            "of the service before a change."
        ),
        sources=[chunk],
    )

    data_agent = Mock()

    critic = make_critic(
        decision=CriticDecision.ACCEPT,
    )

    llm_client = Mock()

    llm_client.generate.return_value = (
        "These checks establish the current service state "
        "and help distinguish existing issues from problems "
        "introduced by a change."
    )

    graph = build_graph(
        orchestrator=orchestrator,
        rag_service=rag_service,
        data_agent=data_agent,
        critic_agent=critic,
        llm_client=llm_client,
    )

    result = graph.invoke(
        {
            "original_query": query,
            "attempt": 0,
            "max_retries": 2,
            "history": [],
        },
        context=make_context(),
    )

    assert result["route"] == "KNOWLEDGE"

    assert result["final_answer"] == (
        "These checks establish the current service state "
        "and help distinguish existing issues from problems "
        "introduced by a change."
    )

    assert result["critique"] is not None

    assert result["critique"].decision == (
        CriticDecision.ACCEPT
    )

    assert result["critique"].retry_target is None

    assert rag_service.answer.call_count == 1

    assert data_agent.invoke.call_count == 0

    assert critic.evaluate.call_count == 1

    critic_call = critic.evaluate.call_args

    assert critic_call.kwargs["query"] == query

    assert critic_call.kwargs["answer"] == (
        "These checks establish the current service state "
        "and help distinguish existing issues from problems "
        "introduced by a change."
    )

    assert critic_call.kwargs["chunks"] == [
        chunk
    ]

    assert (
        critic_call.kwargs["database_result"]
        is None
    )

    # ------------------------------------------------------------------
    # Existing graph-node assertions
    # ------------------------------------------------------------------

    nodes = history_nodes(result)

    assert "orchestrator" in nodes
    assert "knowledge_agent" in nodes
    assert "synthesis" in nodes
    assert "multi_agent_critic" in nodes
    assert "finalize" in nodes

    # ------------------------------------------------------------------
    # NEW: Agent execution observability assertions
    # ------------------------------------------------------------------

    execution_events = [
        event
        for event in result["history"]
        if event.get("node") == "agent_execution"
    ]

    assert execution_events

    knowledge_execution = next(
        event
        for event in execution_events
        if event["agent_name"] == "knowledge_agent"
    )

    assert knowledge_execution["status"] == "SUCCESS"

    assert knowledge_execution["latency_ms"] >= 0

    assert (
        knowledge_execution["details"]["retrieved_chunks"]
        == 1
    )


# ===========================================================================
# 2. DATABASE ROUTE
# ===========================================================================


def test_database_route_is_critic_evaluated():

    query = "What is my email?"

    database_answer = (
        "Your email is abhishek@example.com."
    )

    orchestrator = make_orchestrator(
        route=AgentRoute.DATABASE,
        database_query=query,
        reason=(
            "The query requires structured enterprise data."
        ),
    )

    rag_service = Mock()

    data_agent = Mock()

    data_agent.invoke.return_value = (
        database_answer
    )

    critic = make_critic(
        decision=CriticDecision.ACCEPT,
    )

    llm_client = Mock()

    llm_client.generate.return_value = (
        database_answer
    )

    graph = build_graph(
        orchestrator=orchestrator,
        rag_service=rag_service,
        data_agent=data_agent,
        critic_agent=critic,
        llm_client=llm_client,
    )

    context = make_context()

    result = graph.invoke(
        {
            "original_query": query,
            "attempt": 0,
            "max_retries": 2,
            "history": [],
        },
        context=context,
    )

    assert result["route"] == "DATABASE"

    assert result["database_result"] == (
        database_answer
    )

    assert result["final_answer"] == (
        database_answer
    )

    assert rag_service.answer.call_count == 0

    assert data_agent.invoke.call_count == 1

    data_call = (
        data_agent.invoke.call_args
    )

    assert data_call.kwargs["query"] == query

    assert data_call.kwargs["db"] is context.db

    assert (
        data_call.kwargs["current_user"]
        is context.current_user
    )

    # NEW BEHAVIOR:
    # Database evidence is now evaluated.
    assert critic.evaluate.call_count == 1

    critic_call = (
        critic.evaluate.call_args
    )

    assert critic_call.kwargs["query"] == query

    assert critic_call.kwargs["answer"] == (
        database_answer
    )

    assert critic_call.kwargs["chunks"] == []

    assert critic_call.kwargs[
        "database_result"
    ] == database_answer

    assert result["critique"] is not None

    assert result["critique"].decision == (
        CriticDecision.ACCEPT
    )

    nodes = history_nodes(result)

    assert "orchestrator" in nodes
    assert "database_agent" in nodes
    assert "synthesis" in nodes
    assert "multi_agent_critic" in nodes
    assert "finalize" in nodes

    assert "knowledge_agent" not in nodes


# ===========================================================================
# 3. HYBRID ROUTE
# ===========================================================================


def test_hybrid_route_evaluates_both_evidence_sources():

    query = (
        "What is my department and what does its "
        "access policy say?"
    )

    chunk = make_chunk(
        document_id=42,
        original_filename=(
            "engineering_access_policy.pdf"
        ),
        chunk_text=(
            "Engineering employees must request "
            "system access through the approved process."
        ),
    )

    database_answer = (
        "The current user belongs to the Engineering department."
    )

    final_answer = (
        "You are in the Engineering department. "
        "Its access policy requires employees to request "
        "system access through the approved process."
    )

    orchestrator = make_orchestrator(
        route=AgentRoute.HYBRID,
        knowledge_query=(
            "What does the Engineering department "
            "access policy say?"
        ),
        database_query=(
            "What department does the current user belong to?"
        ),
        reason=(
            "The query requires both user data and "
            "document knowledge."
        ),
    )

    rag_service = Mock()

    rag_service.answer.return_value = make_rag_result(
        query=(
            "What does the Engineering department "
            "access policy say?"
        ),
        answer=(
            "Engineering employees must request "
            "system access through the approved process."
        ),
        sources=[chunk],
    )

    data_agent = Mock()

    data_agent.invoke.return_value = (
        database_answer
    )

    critic = make_critic(
        decision=CriticDecision.ACCEPT,
    )

    llm_client = Mock()

    llm_client.generate.return_value = (
        final_answer
    )

    graph = build_graph(
        orchestrator=orchestrator,
        rag_service=rag_service,
        data_agent=data_agent,
        critic_agent=critic,
        llm_client=llm_client,
    )

    result = graph.invoke(
        {
            "original_query": query,
            "attempt": 0,
            "max_retries": 2,
            "history": [],
        },
        context=make_context(),
    )

    assert result["route"] == "HYBRID"

    assert rag_service.answer.call_count == 1

    assert data_agent.invoke.call_count == 1

    assert result["final_answer"] == final_answer

    assert critic.evaluate.call_count == 1

    critic_call = (
        critic.evaluate.call_args
    )

    assert critic_call.kwargs["query"] == query

    assert critic_call.kwargs["answer"] == (
        final_answer
    )

    assert critic_call.kwargs["chunks"] == [
        chunk
    ]

    assert critic_call.kwargs[
        "database_result"
    ] == database_answer

    assert result["critique"].decision == (
        CriticDecision.ACCEPT
    )

    assert result["critique"].retry_target is None

    # ------------------------------------------------------------------
    # Existing graph-node assertions
    # ------------------------------------------------------------------

    nodes = history_nodes(result)

    assert "orchestrator" in nodes
    assert "knowledge_agent" in nodes
    assert "database_agent" in nodes
    assert "synthesis" in nodes
    assert "multi_agent_critic" in nodes
    assert "finalize" in nodes

    # ------------------------------------------------------------------
    # NEW: Verify every Hybrid execution was traced
    # ------------------------------------------------------------------

    execution_agents = [
        event["agent_name"]
        for event in result["history"]
        if event.get("node") == "agent_execution"
    ]

    assert "orchestrator" in execution_agents
    assert "knowledge_agent" in execution_agents
    assert "database_agent" in execution_agents
    assert "synthesis" in execution_agents
    assert "multi_agent_critic" in execution_agents
    assert "finalize" in execution_agents


# ===========================================================================
# 4. KNOWLEDGE RETRY
# ===========================================================================


def test_knowledge_route_retries_with_improved_query():

    original_query = (
        "Why are those checks important?"
    )

    improved_query = (
        "Why are service health, recent deployments, "
        "active incidents, and monitoring checks important?"
    )

    first_chunk = make_chunk(
        chunk_text=(
            "The system contains operational information."
        )
    )

    second_chunk = make_chunk(
        chunk_text=(
            "Operators should check service health, "
            "recent deployments, active incidents, "
            "and monitoring state before changes."
        )
    )

    orchestrator = make_orchestrator(
        route=AgentRoute.KNOWLEDGE,
        knowledge_query=original_query,
    )

    rag_service = Mock()

    rag_service.answer.side_effect = [
        make_rag_result(
            query=original_query,
            answer="Weak answer.",
            sources=[first_chunk],
        ),
        make_rag_result(
            query=improved_query,
            answer=(
                "Those checks establish the current "
                "state of the service before a change."
            ),
            sources=[second_chunk],
        ),
    ]

    data_agent = Mock()

    critic = Mock()

    critic.evaluate.side_effect = [
        CriticResult(
            decision=CriticDecision.RETRY,
            context_relevance=0.40,
            faithfulness=0.90,
            answer_correctness=0.50,
            reason="The context is insufficient.",
            retry_target=RetryTarget.KNOWLEDGE,
            improved_query=improved_query,
        ),
        CriticResult(
            decision=CriticDecision.ACCEPT,
            context_relevance=0.95,
            faithfulness=0.96,
            answer_correctness=0.95,
            reason="The improved answer is grounded.",
            retry_target=None,
            improved_query=None,
        ),
    ]

    llm_client = Mock()

    llm_client.generate.return_value = (
        "Those checks establish the current state "
        "of the service before a change."
    )

    graph = build_graph(
        orchestrator=orchestrator,
        rag_service=rag_service,
        data_agent=data_agent,
        critic_agent=critic,
        llm_client=llm_client,
    )

    result = graph.invoke(
        {
            "original_query": original_query,
            "attempt": 0,
            "max_retries": 2,
            "history": [],
        },
        context=make_context(),
    )

    assert result["final_answer"] == (
        "Those checks establish the current state "
        "of the service before a change."
    )

    assert rag_service.answer.call_count == 2

    assert (
        rag_service.answer.call_args_list[0]
        .kwargs["query"]
        == original_query
    )

    assert (
        rag_service.answer.call_args_list[1]
        .kwargs["query"]
        == improved_query
    )

    assert critic.evaluate.call_count == 2

    assert result["attempt"] == 2

    assert result["retry_target"] is None

    retry_events = [
        event
        for event in result["history"]
        if event.get("node") == "prepare_retry"
    ]

    assert len(retry_events) == 1

    assert retry_events[0]["retry_target"] == (
        "KNOWLEDGE"
    )

    # ------------------------------------------------------------------
    # Existing retry execution assertion
    # ------------------------------------------------------------------

    knowledge_events = [
        event
        for event in result["history"]
        if event.get("node")
        == "knowledge_agent"
    ]

    assert len(knowledge_events) == 2

    # ------------------------------------------------------------------
    # NEW: Observability must record both executions
    # ------------------------------------------------------------------

    knowledge_execution_events = [
        event
        for event in result["history"]
        if (
            event.get("node") == "agent_execution"
            and event.get("agent_name")
            == "knowledge_agent"
        )
    ]

    assert len(knowledge_execution_events) == 2


# ===========================================================================
# 5. DATABASE RETRY
# ===========================================================================


def test_database_route_retries_database_agent():

    query = "What is my department?"

    improved_query = (
        "Find the current user's department and team."
    )

    orchestrator = make_orchestrator(
        route=AgentRoute.DATABASE,
        database_query=query,
    )

    rag_service = Mock()

    data_agent = Mock()

    data_agent.invoke.side_effect = [
        "The user is in Engineering.",
        (
            "The user is in Engineering and belongs "
            "to the Platform team."
        ),
    ]

    critic = Mock()

    critic.evaluate.side_effect = [
        CriticResult(
            decision=CriticDecision.RETRY,
            context_relevance=0.50,
            faithfulness=0.60,
            answer_correctness=0.55,
            reason="The database evidence is incomplete.",
            retry_target=RetryTarget.DATABASE,
            improved_query=improved_query,
        ),
        CriticResult(
            decision=CriticDecision.ACCEPT,
            context_relevance=0.95,
            faithfulness=0.95,
            answer_correctness=0.95,
            reason="Database evidence is now sufficient.",
            retry_target=None,
            improved_query=None,
        ),
    ]

    llm_client = Mock()

    llm_client.generate.side_effect = [
        "The user is in Engineering.",
        (
            "The user is in Engineering and belongs "
            "to the Platform team."
        ),
    ]

    graph = build_graph(
        orchestrator=orchestrator,
        rag_service=rag_service,
        data_agent=data_agent,
        critic_agent=critic,
        llm_client=llm_client,
    )

    result = graph.invoke(
        {
            "original_query": query,
            "attempt": 0,
            "max_retries": 2,
            "history": [],
        },
        context=make_context(),
    )

    assert data_agent.invoke.call_count == 2

    first_query = (
        data_agent.invoke.call_args_list[0]
        .kwargs["query"]
    )

    second_query = (
        data_agent.invoke.call_args_list[1]
        .kwargs["query"]
    )

    assert first_query == query

    assert second_query == improved_query

    assert critic.evaluate.call_count == 2

    assert result["final_answer"] == (
        "The user is in Engineering and belongs "
        "to the Platform team."
    )

    assert result["critique"].decision == (
        CriticDecision.ACCEPT
    )


# ===========================================================================
# 6. HYBRID RETRY — BOTH
# ===========================================================================


def test_hybrid_route_can_retry_both_agents():

    query = (
        "What is my department and what does "
        "its policy say?"
    )

    improved_query = (
        "Find my department and retrieve the "
        "department access policy."
    )

    chunk = make_chunk(
        original_filename="engineering_policy.pdf",
        chunk_text=(
            "Engineering employees must use the "
            "approved access request process."
        ),
    )

    orchestrator = make_orchestrator(
        route=AgentRoute.HYBRID,
        knowledge_query="department access policy",
        database_query="current user department",
    )

    rag_service = Mock()

    rag_service.answer.side_effect = [
        make_rag_result(
            query="department access policy",
            answer="Weak policy context.",
            sources=[chunk],
        ),
        make_rag_result(
            query=improved_query,
            answer=(
                "Engineering employees must use "
                "the approved access request process."
            ),
            sources=[chunk],
        ),
    ]

    data_agent = Mock()

    data_agent.invoke.side_effect = [
        "Engineering.",
        "Engineering department.",
    ]

    critic = Mock()

    critic.evaluate.side_effect = [
        CriticResult(
            decision=CriticDecision.RETRY,
            context_relevance=0.50,
            faithfulness=0.50,
            answer_correctness=0.50,
            reason="Both evidence sources need improvement.",
            retry_target=RetryTarget.BOTH,
            improved_query=improved_query,
        ),
        CriticResult(
            decision=CriticDecision.ACCEPT,
            context_relevance=0.95,
            faithfulness=0.95,
            answer_correctness=0.95,
            reason="Both evidence sources now support the answer.",
            retry_target=None,
            improved_query=None,
        ),
    ]

    llm_client = Mock()

    llm_client.generate.side_effect = [
        "Initial synthesized answer.",
        (
            "You are in Engineering. "
            "Engineering employees must use "
            "the approved access request process."
        ),
    ]

    graph = build_graph(
        orchestrator=orchestrator,
        rag_service=rag_service,
        data_agent=data_agent,
        critic_agent=critic,
        llm_client=llm_client,
    )

    result = graph.invoke(
        {
            "original_query": query,
            "attempt": 0,
            "max_retries": 2,
            "history": [],
        },
        context=make_context(),
    )

    # Both specialists ran initially and again.
    assert rag_service.answer.call_count == 2

    assert data_agent.invoke.call_count == 2

    assert critic.evaluate.call_count == 2

    assert result["final_answer"] == (
        "You are in Engineering. "
        "Engineering employees must use "
        "the approved access request process."
    )

    assert result["critique"].decision == (
        CriticDecision.ACCEPT
    )

    # Both branches should have executed again.
    knowledge_events = [
        event
        for event in result["history"]
        if event.get("node")
        == "knowledge_agent"
    ]

    database_events = [
        event
        for event in result["history"]
        if event.get("node")
        == "database_agent"
    ]

    assert len(knowledge_events) == 2

    assert len(database_events) == 2


# ===========================================================================
# 7. RETRY LIMIT
# ===========================================================================


def test_retry_limit_is_enforced():

    query = "Explain the system."

    chunk = make_chunk()

    orchestrator = make_orchestrator(
        route=AgentRoute.KNOWLEDGE,
        knowledge_query=query,
    )

    rag_service = Mock()

    rag_service.answer.return_value = make_rag_result(
        query=query,
        answer="Still weak.",
        sources=[chunk],
    )

    data_agent = Mock()

    critic = Mock()

    critic.evaluate.return_value = (
        CriticResult(
            decision=CriticDecision.RETRY,
            context_relevance=0.30,
            faithfulness=0.30,
            answer_correctness=0.30,
            reason="Still insufficient.",
            retry_target=RetryTarget.KNOWLEDGE,
            improved_query="Improve the query.",
        )
    )

    llm_client = Mock()

    llm_client.generate.return_value = (
        "Still weak."
    )

    graph = build_graph(
        orchestrator=orchestrator,
        rag_service=rag_service,
        data_agent=data_agent,
        critic_agent=critic,
        llm_client=llm_client,
    )

    result = graph.invoke(
        {
            "original_query": query,
            "attempt": 0,
            "max_retries": 2,
            "history": [],
        },
        context=make_context(),
    )

    # Initial generation + 2 retries.
    assert rag_service.answer.call_count == 3

    assert critic.evaluate.call_count == 3

    assert result["final_answer"] == (
        "Still weak."
    )


# ===========================================================================
# 8. NO EVIDENCE
# ===========================================================================


def test_knowledge_route_with_no_context_skips_critic():

    query = (
        "Something not present in the KB."
    )

    orchestrator = make_orchestrator(
        route=AgentRoute.KNOWLEDGE,
        knowledge_query=query,
    )

    rag_service = Mock()

    rag_service.answer.return_value = make_rag_result(
        query=query,
        answer=(
            "I could not find enough information "
            "in the knowledge base."
        ),
        sources=[],
    )

    data_agent = Mock()

    critic = Mock()

    llm_client = Mock()

    llm_client.generate.return_value = (
        "I could not find enough information "
        "in the knowledge base."
    )

    graph = build_graph(
        orchestrator=orchestrator,
        rag_service=rag_service,
        data_agent=data_agent,
        critic_agent=critic,
        llm_client=llm_client,
    )

    result = graph.invoke(
        {
            "original_query": query,
            "attempt": 0,
            "max_retries": 2,
            "history": [],
        },
        context=make_context(),
    )

    assert result["final_answer"] == (
        "I could not find enough information "
        "in the knowledge base."
    )

    assert rag_service.answer.call_count == 1

    assert critic.evaluate.call_count == 0


# ===========================================================================
# 9. ORCHESTRATOR ROUTING
# ===========================================================================


@pytest.mark.parametrize(
    "route",
    [
        AgentRoute.KNOWLEDGE,
        AgentRoute.DATABASE,
        AgentRoute.HYBRID,
    ],
)
def test_orchestrator_route_is_preserved(
    route,
):

    orchestrator = make_orchestrator(
        route=route,
        reason="Test routing.",
    )

    rag_service = Mock()

    rag_service.answer.return_value = make_rag_result(
        query="test",
        answer="Knowledge answer.",
        sources=[make_chunk()],
    )

    data_agent = Mock()

    data_agent.invoke.return_value = (
        "Database answer."
    )

    critic = make_critic(
        decision=CriticDecision.ACCEPT,
    )

    llm_client = Mock()

    llm_client.generate.return_value = (
        "Final answer."
    )

    graph = build_graph(
        orchestrator=orchestrator,
        rag_service=rag_service,
        data_agent=data_agent,
        critic_agent=critic,
        llm_client=llm_client,
    )

    result = graph.invoke(
        {
            "original_query": "test",
            "attempt": 0,
            "max_retries": 2,
            "history": [],
        },
        context=make_context(),
    )

    assert result["route"] == (
        route.value
    )


# ===========================================================================
# 10. RUNTIME CONTEXT
# ===========================================================================


def test_graph_passes_runtime_context_to_database_agent():

    orchestrator = make_orchestrator(
        route=AgentRoute.DATABASE,
        database_query="What is my email?",
    )

    rag_service = Mock()

    data_agent = Mock()

    data_agent.invoke.return_value = (
        "Your email is abhishek@example.com."
    )

    critic = make_critic(
        decision=CriticDecision.ACCEPT,
    )

    llm_client = Mock()

    llm_client.generate.return_value = (
        "Your email is abhishek@example.com."
    )

    graph = build_graph(
        orchestrator=orchestrator,
        rag_service=rag_service,
        data_agent=data_agent,
        critic_agent=critic,
        llm_client=llm_client,
    )

    context = make_context()

    graph.invoke(
        {
            "original_query": "What is my email?",
            "attempt": 0,
            "max_retries": 2,
            "history": [],
        },
        context=context,
    )

    assert data_agent.invoke.call_count == 1

    call = data_agent.invoke.call_args

    assert call.kwargs["db"] is context.db

    assert (
        call.kwargs["current_user"]
        is context.current_user
    )