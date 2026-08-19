from unittest.mock import Mock

import pytest

from app.agents.critic_agent import (
    CriticAgent,
    CriticDecision,
)
def make_chunk():

    chunk = Mock()

    chunk.document_id = 35
    chunk.original_filename = (
        "02_organization_it_operations.pdf"
    )
    chunk.chunk_text = (
        "Operators should check service health, "
        "recent deployments, active incidents, "
        "and monitoring state before changing a service."
    )

    return chunk


def make_agent():

    llm = Mock()

    llm.generate.return_value = """
    {
        "decision": "ACCEPT",
        "context_relevance": 0.95,
        "faithfulness": 0.94,
        "answer_correctness": 0.92,
        "reason": "The answer is well supported.",
        "improved_query": null
    }
    """

    return CriticAgent(
        llm_client=llm,
    ), llm


def test_valid_critique_is_parsed():

    agent, llm = make_agent()

    result = agent.evaluate(
        query="Why are these checks important?",
        answer=(
            "They establish the current state of "
            "the service before a change."
        ),
        chunks=[make_chunk()],
    )

    assert result.decision == CriticDecision.ACCEPT
    assert result.context_relevance == pytest.approx(
        0.95
    )
    assert result.faithfulness == pytest.approx(
        0.94
    )
    assert result.answer_correctness == pytest.approx(
        0.92
    )

    llm.generate.assert_called_once()


def test_retry_requires_improved_query():

    agent, llm = make_agent()

    llm.generate.return_value = """
    {
        "decision": "RETRY",
        "context_relevance": 0.40,
        "faithfulness": 0.70,
        "answer_correctness": 0.50,
        "reason": "Context is insufficient.",
        "improved_query": "Why are service monitoring checks important?"
    }
    """

    result = agent.evaluate(
        query="Why are these checks important?",
        answer="They are important.",
        chunks=[make_chunk()],
    )

    assert result.decision == CriticDecision.RETRY

    assert result.improved_query == (
        "Why are service monitoring checks important?"
    )


def test_retry_without_query_is_rejected():

    agent, llm = make_agent()

    llm.generate.return_value = """
    {
        "decision": "RETRY",
        "context_relevance": 0.40,
        "faithfulness": 0.70,
        "answer_correctness": 0.50,
        "reason": "Context is insufficient.",
        "improved_query": null
    }
    """

    with pytest.raises(
        RuntimeError,
        match="without an improved query",
    ):
        agent.evaluate(
            query="test",
            answer="test",
            chunks=[make_chunk()],
        )


def test_empty_query_is_rejected():

    agent, _ = make_agent()

    with pytest.raises(
        ValueError,
        match="Query cannot be empty",
    ):
        agent.evaluate(
            query="",
            answer="test",
            chunks=[make_chunk()],
        )


def test_empty_answer_is_rejected():

    agent, _ = make_agent()

    with pytest.raises(
        ValueError,
        match="Answer cannot be empty",
    ):
        agent.evaluate(
            query="test",
            answer="",
            chunks=[make_chunk()],
        )


def test_empty_context_is_rejected():

    agent, _ = make_agent()

    with pytest.raises(
        ValueError,
        match="retrieved context",
    ):
        agent.evaluate(
            query="test",
            answer="test",
            chunks=[],
        )


def test_markdown_json_is_supported():

    agent, llm = make_agent()

    llm.generate.return_value = """
    ```json
    {
        "decision": "ACCEPT",
        "context_relevance": 1.0,
        "faithfulness": 1.0,
        "answer_correctness": 1.0,
        "reason": "Fully supported.",
        "improved_query": null
    }
    ```
    """

    result = agent.evaluate(
        query="test",
        answer="test",
        chunks=[make_chunk()],
    )

    assert result.decision == CriticDecision.ACCEPT