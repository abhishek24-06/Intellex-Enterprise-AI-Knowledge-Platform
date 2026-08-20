from types import SimpleNamespace
from unittest.mock import Mock

from app.agents.critic_agent import (
    CriticDecision,
    CriticResult,
)
from app.agents.graph.graph import (
    build_rag_graph_agent
)
from app.dto.rag_response import RAGResult


def make_chunk():

    return SimpleNamespace(
        document_id=35,
        original_filename=(
            "02_organization_it_operations.pdf"
        ),
        chunk_text=(
            "Service health and recent deployments "
            "should be checked before changes."
        ),
    )


def make_context():

    return SimpleNamespace(
        db=Mock(),
        current_user=Mock(
            user_id=4,
            organization_id=2,
        ),
    )


def test_graph_accepts_first_answer():

    rag_service = Mock()

    rag_service.answer.return_value = RAGResult(
        query="test",
        answer="Grounded answer.",
        sources=[make_chunk()],
    )

    critic = Mock()

    critic.evaluate.return_value = CriticResult(
        decision=CriticDecision.ACCEPT,
        context_relevance=0.95,
        faithfulness=0.95,
        answer_correctness=0.95,
        reason="Supported.",
    )

    graph = build_rag_graph_agent(
        rag_service=rag_service,
        critic_agent=critic,
        max_retries=2,
    )

    result = graph.invoke(
        {
            "original_query": "test",
            "retrieval_query": "test",
            "attempt": 0,
            "max_retries": 2,
            "history": [],
        },
        context=make_context(),
    )

    assert result["final_answer"] == (
        "Grounded answer."
    )

    assert (
        rag_service.answer.call_count
        == 1
    )

    assert (
        critic.evaluate.call_count
        == 1
    )


def test_graph_retries_with_improved_query():

    rag_service = Mock()

    chunk = make_chunk()

    rag_service.answer.side_effect = [
        RAGResult(
            query="Why are these checks important?",
            answer="Weak answer.",
            sources=[chunk],
        ),
        RAGResult(
            query=(
                "Why are service monitoring checks important?"
            ),
            answer="Better grounded answer.",
            sources=[chunk],
        ),
    ]

    critic = Mock()

    critic.evaluate.side_effect = [
        CriticResult(
            decision=CriticDecision.RETRY,
            context_relevance=0.40,
            faithfulness=0.70,
            answer_correctness=0.50,
            reason="Insufficient context.",
            improved_query=(
                "Why are service monitoring checks important?"
            ),
        ),
        CriticResult(
            decision=CriticDecision.ACCEPT,
            context_relevance=0.95,
            faithfulness=0.96,
            answer_correctness=0.94,
            reason="Supported.",
        ),
    ]

    graph = build_rag_graph_agent(
        rag_service=rag_service,
        critic_agent=critic,
        max_retries=2,
    )

    result = graph.invoke(
        {
            "original_query": (
                "Why are these checks important?"
            ),
            "retrieval_query": (
                "Why are these checks important?"
            ),
            "attempt": 0,
            "max_retries": 2,
            "history": [],
        },
        context=make_context(),
    )

    assert result["final_answer"] == (
        "Better grounded answer."
    )

    assert rag_service.answer.call_count == 2

    assert (
        rag_service.answer.call_args_list[1]
        .kwargs["query"]
        == "Why are service monitoring checks important?"
    )


def test_graph_stops_after_retry_limit():

    chunk = make_chunk()

    rag_service = Mock()

    rag_service.answer.return_value = RAGResult(
        query="test",
        answer="Still weak.",
        sources=[chunk],
    )

    critic = Mock()

    critic.evaluate.return_value = CriticResult(
        decision=CriticDecision.RETRY,
        context_relevance=0.20,
        faithfulness=0.20,
        answer_correctness=0.20,
        reason="Bad answer.",
        improved_query="better query",
    )

    graph = build_rag_graph_agent(
        rag_service=rag_service,
        critic_agent=critic,
        max_retries=2,
    )

    result = graph.invoke(
        {
            "original_query": "test",
            "retrieval_query": "test",
            "attempt": 0,
            "max_retries": 2,
            "history": [],
        },
        context=make_context(),
    )

    assert result["final_answer"] == (
        "Still weak."
    )

    assert rag_service.answer.call_count == 3