from unittest.mock import Mock

import pytest

from app.agents.critic_agent import (
    CriticDecision,
    CriticResult,
)
from app.agents.self_correcting_rag_service import (
    SelfCorrectingRAGService,
)
from app.dto.rag_response import RAGResult


def make_rag_result(
    *,
    query: str,
    answer: str = "Draft answer.",
    sources=None,
):

    return RAGResult(
        query=query,
        answer=answer,
        sources=sources or [],
    )


def make_chunk():

    chunk = Mock()

    chunk.document_id = 35
    chunk.original_filename = (
        "02_organization_it_operations.pdf"
    )
    chunk.chunk_text = (
        "Service health and recent deployments "
        "should be checked before changes."
    )

    return chunk


def test_accept_returns_first_answer():

    rag_service = Mock()

    chunk = make_chunk()

    rag_service.answer.return_value = (
        make_rag_result(
            query="test",
            sources=[chunk],
        )
    )

    critic = Mock()

    critic.evaluate.return_value = CriticResult(
        decision=CriticDecision.ACCEPT,
        context_relevance=0.95,
        faithfulness=0.95,
        answer_correctness=0.95,
        reason="Good answer.",
    )

    service = SelfCorrectingRAGService(
        rag_service=rag_service,
        critic_agent=critic,
        max_retries=2,
    )

    result = service.answer(
        db=Mock(),
        query="test",
        current_user=Mock(),
    )

    assert result.answer == "Draft answer."

    rag_service.answer.assert_called_once()

    critic.evaluate.assert_called_once()


def test_retry_uses_improved_query():

    rag_service = Mock()

    chunk = make_chunk()

    rag_service.answer.side_effect = [
        make_rag_result(
            query="Why are these checks important?",
            answer="Weak answer.",
            sources=[chunk],
        ),
        make_rag_result(
            query="Why are service monitoring checks important?",
            answer="Better answer.",
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
            reason="Weak context.",
            improved_query=(
                "Why are service monitoring checks important?"
            ),
        ),
        CriticResult(
            decision=CriticDecision.ACCEPT,
            context_relevance=0.95,
            faithfulness=0.94,
            answer_correctness=0.93,
            reason="Supported.",
        ),
    ]

    service = SelfCorrectingRAGService(
        rag_service=rag_service,
        critic_agent=critic,
        max_retries=2,
    )

    result = service.answer(
        db=Mock(),
        query="Why are these checks important?",
        current_user=Mock(),
    )

    assert result.answer == "Better answer."

    assert rag_service.answer.call_count == 2

    first_call = rag_service.answer.call_args_list[0]
    second_call = rag_service.answer.call_args_list[1]

    assert first_call.kwargs["query"] == (
        "Why are these checks important?"
    )

    assert second_call.kwargs["query"] == (
        "Why are service monitoring checks important?"
    )


def test_retry_limit_is_enforced():

    rag_service = Mock()

    chunk = make_chunk()

    rag_service.answer.return_value = (
        make_rag_result(
            query="test",
            answer="Still weak.",
            sources=[chunk],
        )
    )

    critic = Mock()

    critic.evaluate.side_effect = [
        CriticResult(
            decision=CriticDecision.RETRY,
            context_relevance=0.30,
            faithfulness=0.30,
            answer_correctness=0.30,
            reason="Still insufficient.",
            improved_query="better query 1",
        ),
        CriticResult(   
            decision=CriticDecision.RETRY,
            context_relevance=0.30,
            faithfulness=0.30,
            answer_correctness=0.30,
            reason="Still insufficient.",
            improved_query="better query 2",
        ),
        CriticResult(
            decision=CriticDecision.RETRY,
            context_relevance=0.30,
            faithfulness=0.30,
            answer_correctness=0.30,
            reason="Still insufficient.",
            improved_query="better query 3",
        ),
    ]

    service = SelfCorrectingRAGService(
        rag_service=rag_service,
        critic_agent=critic,
        max_retries=2,
    )

    result = service.answer(
        db=Mock(),
        query="test",
        current_user=Mock(),
    )

    assert result.answer == "Still weak."

    # Initial attempt + 2 retries
    assert rag_service.answer.call_count == 3

    # Critic evaluates all 3 attempts
    assert critic.evaluate.call_count == 3