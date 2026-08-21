from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from app.agents.critic_agent import (
    CriticDecision,
    CriticResult,
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


# ======================================================================
# Helpers
# ======================================================================


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
    improved_query: str | None = None,
    context_relevance: float = 0.95,
    faithfulness: float = 0.95,
    answer_correctness: float = 0.95,
    reason: str = "Answer is sufficiently grounded.",
):
    critic = Mock()

    critic.evaluate.return_value = CriticResult(
        decision=decision,
        context_relevance=context_relevance,
        faithfulness=faithfulness,
        answer_correctness=answer_correctness,
        reason=reason,
        improved_query=improved_query,
    )

    return critic


def build_graph(
    *,
    orchestrator,
    rag_service,
    data_agent,
    critic_agent,
    llm_client,
    max_retries: int = 2,
):
    """
    Centralized graph construction so all tests use the
    exact same production graph builder.
    """

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
        for item in result.get("history", [])
        if isinstance(item, dict)
        and "node" in item
    }


# ======================================================================
# 1. KNOWLEDGE ROUTE
# ======================================================================


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
        reason="The query requires enterprise document knowledge.",
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

    assert result["knowledge_query"] == (
        "Why are service health, recent deployments, "
        "active incidents, and monitoring checks important?"
    )

    assert result["final_answer"] == (
        "These checks establish the current service state "
        "and help distinguish existing issues from problems "
        "introduced by a change."
    )

    assert result["critique"] is not None

    assert result["critique"].decision == (
        CriticDecision.ACCEPT
    )

    assert rag_service.answer.call_count == 1

    assert data_agent.invoke.call_count == 0

    assert critic.evaluate.call_count == 1

    nodes = history_nodes(result)

    assert "orchestrator" in nodes
    assert "knowledge_agent" in nodes
    assert "synthesis" in nodes
    assert "multi_agent_critic" in nodes
    assert "finalize" in nodes


# ======================================================================
# 2. DATABASE ROUTE
# ======================================================================


def test_database_route_skips_knowledge_and_uses_database_agent():

    query = "What is my email?"

    orchestrator = make_orchestrator(
        route=AgentRoute.DATABASE,
        database_query="What is my email?",
        reason="The query requires user database information.",
    )

    rag_service = Mock()

    data_agent = Mock()

    data_agent.invoke.return_value = (
        "Your email is abhishek@example.com."
    )

    critic = Mock()

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

    assert result["database_query"] == (
        "What is my email?"
    )

    assert result["database_result"] == (
        "Your email is abhishek@example.com."
    )

    assert result["final_answer"] == (
        "Your email is abhishek@example.com."
    )

    assert rag_service.answer.call_count == 0

    assert data_agent.invoke.call_count == 1

    data_call = data_agent.invoke.call_args

    assert data_call.kwargs["query"] == (
        "What is my email?"
    )

    assert data_call.kwargs["db"] is context.db

    assert (
        data_call.kwargs["current_user"]
        is context.current_user
    )

    # DB-only currently has no document context for
    # CriticAgent, so the critic should be skipped.
    assert critic.evaluate.call_count == 0

    nodes = history_nodes(result)

    assert "orchestrator" in nodes
    assert "database_agent" in nodes
    assert "synthesis" in nodes
    assert "finalize" in nodes

    assert "knowledge_agent" not in nodes

    assert (
        "multi_agent_critic"
        in nodes
    )


# ======================================================================
# 3. HYBRID ROUTE
# ======================================================================


def test_hybrid_route_runs_both_agents_before_synthesis():

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
        "The current user belongs to the Engineering department."
    )

    critic = make_critic(
        decision=CriticDecision.ACCEPT,
    )

    llm_client = Mock()

    llm_client.generate.return_value = (
        "You are in the Engineering department. "
        "Its access policy requires employees to request "
        "system access through the approved process."
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

    assert result["knowledge_query"] == (
        "What does the Engineering department "
        "access policy say?"
    )

    assert result["database_query"] == (
        "What department does the current user belong to?"
    )

    assert result["rag_result"] is not None

    assert result["database_result"] == (
        "The current user belongs to the Engineering department."
    )

    assert result["final_answer"] == (
        "You are in the Engineering department. "
        "Its access policy requires employees to request "
        "system access through the approved process."
    )

    # Both agents must run.
    assert rag_service.answer.call_count == 1

    assert data_agent.invoke.call_count == 1

    # Synthesis sees both results.
    assert llm_client.generate.call_count == 1

    synthesis_prompt = (
        llm_client.generate.call_args.kwargs[
            "user_prompt"
        ]
    )

    assert (
        "The current user belongs to the Engineering department."
        in synthesis_prompt
    )

    assert (
        "Engineering employees must request"
        in synthesis_prompt
    )

    # Critic evaluates the synthesized answer.
    assert critic.evaluate.call_count == 1

    assert result["critique"] is not None

    assert result["critique"].decision == (
        CriticDecision.ACCEPT
    )

    nodes = history_nodes(result)

    assert "orchestrator" in nodes
    assert "knowledge_agent" in nodes
    assert "database_agent" in nodes
    assert "synthesis" in nodes
    assert "multi_agent_critic" in nodes
    assert "finalize" in nodes


# ======================================================================
# 4. KNOWLEDGE RETRY / SELF-CORRECTION
# ======================================================================


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
        reason="The query requires document knowledge.",
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
            reason=(
                "The original context does not adequately "
                "answer the ambiguous query."
            ),
            improved_query=improved_query,
        ),
        CriticResult(
            decision=CriticDecision.ACCEPT,
            context_relevance=0.95,
            faithfulness=0.96,
            answer_correctness=0.95,
            reason="The improved answer is grounded.",
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

    first_query = (
        rag_service.answer.call_args_list[0]
        .kwargs["query"]
    )

    second_query = (
        rag_service.answer.call_args_list[1]
        .kwargs["query"]
    )

    assert first_query == original_query

    assert second_query == improved_query

    assert critic.evaluate.call_count == 2

    assert result["attempt"] == 2

    nodes = history_nodes(result)

    # Two knowledge executions should have been recorded.
    knowledge_events = [
        event
        for event in result["history"]
        if event.get("node")
        == "knowledge_agent"
    ]

    assert len(knowledge_events) == 2

    assert "prepare_retry" in nodes
    assert "multi_agent_critic" in nodes
    assert "finalize" in nodes


# ======================================================================
# 5. RETRY LIMIT
# ======================================================================


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

    critic.evaluate.return_value = CriticResult(
        decision=CriticDecision.RETRY,
        context_relevance=0.30,
        faithfulness=0.30,
        answer_correctness=0.30,
        reason="Still insufficient.",
        improved_query="Improve the query.",
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

    # Initial generation + 2 retries = 3.
    assert rag_service.answer.call_count == 3

    # Critic runs after each generated answer.
    assert critic.evaluate.call_count == 3

    assert result["final_answer"] == (
        "Still weak."
    )


# ======================================================================
# 6. NO CONTEXT
# ======================================================================


def test_knowledge_route_with_no_context_finalizes_without_retry():

    query = "Something not present in the KB."

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

    assert result["route"] == "KNOWLEDGE"

    assert result["final_answer"] == (
        "I could not find enough information "
        "in the knowledge base."
    )

    assert rag_service.answer.call_count == 1

    # Synthesis still runs with the no-context result.
    assert llm_client.generate.call_count == 1

    assert critic.evaluate.call_count == 0

    nodes = history_nodes(result)

    assert "knowledge_agent" in nodes
    assert "synthesis" in nodes
    assert "multi_agent_critic" in nodes
    assert "finalize" in nodes


# ======================================================================
# 7. ORCHESTRATOR ROUTING
# ======================================================================


@pytest.mark.parametrize(
    "route",
    [
        AgentRoute.KNOWLEDGE,
        AgentRoute.DATABASE,
        AgentRoute.HYBRID,
    ],
)
def test_orchestrator_route_is_preserved(route):

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

    assert result["route"] == route.value


# ======================================================================
# 8. GRAPH USES AUTHENTICATED RUNTIME CONTEXT
# ======================================================================


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

    critic = Mock()

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