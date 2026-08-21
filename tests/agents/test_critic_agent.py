from __future__ import annotations

from unittest.mock import Mock

import pytest

from app.agents.critic_agent import (
    CriticAgent,
    CriticDecision,
    RetryTarget,
)


# ======================================================================
# Helpers
# ======================================================================


def make_chunk(
    *,
    document_id: int = 35,
    filename: str = (
        "02_organization_it_operations.pdf"
    ),
    content: str = (
        "Operators should check service health, "
        "recent deployments, active incidents, "
        "and monitoring state before changing a service."
    ),
):
    chunk = Mock()

    chunk.document_id = document_id
    chunk.original_filename = filename
    chunk.chunk_text = content

    return chunk


def make_agent():
    llm = Mock()

    llm.generate.return_value = """
    {
        "decision": "ACCEPT",
        "context_relevance": 0.95,
        "faithfulness": 0.94,
        "answer_correctness": 0.93,
        "reason": "The answer is sufficiently supported.",
        "retry_target": null,
        "improved_query": null
    }
    """

    return CriticAgent(
        llm_client=llm,
    ), llm


# ======================================================================
# Basic validation
# ======================================================================


def test_empty_query_is_rejected():

    agent, _ = make_agent()

    with pytest.raises(
        ValueError,
        match="Query cannot be empty",
    ):
        agent.evaluate(
            query="",
            answer="test answer",
            chunks=[make_chunk()],
        )


def test_empty_answer_is_rejected():

    agent, _ = make_agent()

    with pytest.raises(
        ValueError,
        match="Answer cannot be empty",
    ):
        agent.evaluate(
            query="test query",
            answer="",
            chunks=[make_chunk()],
        )


def test_no_evidence_is_rejected():

    agent, _ = make_agent()

    with pytest.raises(
        ValueError,
        match="at least one evidence source",
    ):
        agent.evaluate(
            query="test query",
            answer="test answer",
        )


# ======================================================================
# Knowledge evidence
# ======================================================================


def test_knowledge_evidence_is_evaluated():

    agent, llm = make_agent()

    result = agent.evaluate(
        query="Why are these checks important?",
        answer=(
            "They establish the current state "
            "of the service before a change."
        ),
        chunks=[make_chunk()],
    )

    assert result.decision == (
        CriticDecision.ACCEPT
    )

    assert result.context_relevance == pytest.approx(
        0.95
    )

    assert result.faithfulness == pytest.approx(
        0.94
    )

    assert result.answer_correctness == pytest.approx(
        0.93
    )

    assert result.retry_target is None
    assert result.improved_query is None

    llm.generate.assert_called_once()

    prompt = (
        llm.generate.call_args.kwargs[
            "user_prompt"
        ]
    )

    assert (
        "KNOWLEDGE AGENT EVIDENCE"
        in prompt
    )

    assert (
        "02_organization_it_operations.pdf"
        in prompt
    )

    assert (
        "Operators should check service health"
        in prompt
    )


# ======================================================================
# Database evidence
# ======================================================================


def test_database_evidence_is_evaluated():

    agent, llm = make_agent()

    database_result = (
        "user_id=7; "
        "name=Abhishek; "
        "email=abhishek@example.com; "
        "department=Engineering"
    )

    result = agent.evaluate(
        query="What is my email?",
        answer=(
            "Your email is abhishek@example.com."
        ),
        database_result=database_result,
    )

    assert result.decision == (
        CriticDecision.ACCEPT
    )

    assert result.retry_target is None
    assert result.improved_query is None

    prompt = (
        llm.generate.call_args.kwargs[
            "user_prompt"
        ]
    )

    assert (
        "DATABASE AGENT EVIDENCE"
        in prompt
    )

    assert (
        "abhishek@example.com"
        in prompt
    )


# ======================================================================
# Hybrid evidence
# ======================================================================


def test_hybrid_evidence_is_evaluated():

    agent, llm = make_agent()

    chunk = make_chunk(
        filename="engineering_access_policy.pdf",
        content=(
            "Engineering employees must request "
            "system access through the approved process."
        ),
    )

    database_result = (
        "user_id=7; department=Engineering"
    )

    result = agent.evaluate(
        query=(
            "What is my department and what does "
            "its access policy say?"
        ),
        answer=(
            "You are in Engineering. Its access policy "
            "requires employees to request system access "
            "through the approved process."
        ),
        chunks=[chunk],
        database_result=database_result,
    )

    assert result.decision == (
        CriticDecision.ACCEPT
    )

    assert result.retry_target is None
    assert result.improved_query is None

    prompt = (
        llm.generate.call_args.kwargs[
            "user_prompt"
        ]
    )

    assert (
        "KNOWLEDGE AGENT EVIDENCE"
        in prompt
    )

    assert (
        "DATABASE AGENT EVIDENCE"
        in prompt
    )

    assert (
        "engineering_access_policy.pdf"
        in prompt
    )

    assert (
        "department=Engineering"
        in prompt
    )


# ======================================================================
# Threshold logic
# ======================================================================


def test_low_score_forces_retry():

    agent, llm = make_agent()

    llm.generate.return_value = """
    {
        "decision": "ACCEPT",
        "context_relevance": 0.70,
        "faithfulness": 0.95,
        "answer_correctness": 0.95,
        "reason": "The retrieved context is weak.",
        "retry_target": "KNOWLEDGE",
        "improved_query": "Improve the knowledge retrieval query."
    }
    """

    result = agent.evaluate(
        query="Why are these checks important?",
        answer="Weak answer.",
        chunks=[make_chunk()],
    )

    assert result.decision == (
        CriticDecision.RETRY
    )

    assert result.retry_target == (
        RetryTarget.KNOWLEDGE
    )

    assert result.improved_query == (
        "Improve the knowledge retrieval query."
    )


# ======================================================================
# Retry target validation
# ======================================================================


def test_retry_without_retry_target_is_rejected():

    agent, llm = make_agent()

    llm.generate.return_value = """
    {
        "decision": "RETRY",
        "context_relevance": 0.40,
        "faithfulness": 0.70,
        "answer_correctness": 0.50,
        "reason": "The answer is insufficient.",
        "retry_target": null,
        "improved_query": "Improve the query."
    }
    """

    with pytest.raises(
        RuntimeError,
        match="retry_target",
    ):
        agent.evaluate(
            query="test query",
            answer="test answer",
            chunks=[make_chunk()],
        )


def test_retry_without_improved_query_is_rejected():

    agent, llm = make_agent()

    llm.generate.return_value = """
    {
        "decision": "RETRY",
        "context_relevance": 0.40,
        "faithfulness": 0.70,
        "answer_correctness": 0.50,
        "reason": "The answer is insufficient.",
        "retry_target": "KNOWLEDGE",
        "improved_query": null
    }
    """

    with pytest.raises(
        RuntimeError,
        match="improved query",
    ):
        agent.evaluate(
            query="test query",
            answer="test answer",
            chunks=[make_chunk()],
        )


@pytest.mark.parametrize(
    "retry_target",
    [
        "KNOWLEDGE",
        "DATABASE",
        "BOTH",
    ],
)
def test_all_retry_targets_are_supported(
    retry_target,
):

    agent, llm = make_agent()

    llm.generate.return_value = f"""
    {{
        "decision": "RETRY",
        "context_relevance": 0.40,
        "faithfulness": 0.70,
        "answer_correctness": 0.50,
        "reason": "The answer is insufficient.",
        "retry_target": "{retry_target}",
        "improved_query": "Improve the query."
    }}
    """

    result = agent.evaluate(
        query="test query",
        answer="test answer",
        chunks=[make_chunk()],
    )

    assert result.decision == (
        CriticDecision.RETRY
    )

    assert result.retry_target.value == (
        retry_target
    )


# ======================================================================
# Database-specific retry
# ======================================================================


def test_database_retry_is_supported():

    agent, llm = make_agent()

    llm.generate.return_value = """
    {
        "decision": "RETRY",
        "context_relevance": 0.50,
        "faithfulness": 0.60,
        "answer_correctness": 0.55,
        "reason": "The database evidence is incomplete.",
        "retry_target": "DATABASE",
        "improved_query": "Find the current user's department and team."
    }
    """

    result = agent.evaluate(
        query=(
            "What is my department and team?"
        ),
        answer=(
            "You are in Engineering."
        ),
        database_result=(
            "user_id=7; department=Engineering"
        ),
    )

    assert result.decision == (
        CriticDecision.RETRY
    )

    assert result.retry_target == (
        RetryTarget.DATABASE
    )

    assert result.improved_query == (
        "Find the current user's department and team."
    )


# ======================================================================
# Hybrid retry
# ======================================================================


def test_hybrid_retry_is_supported():

    agent, llm = make_agent()

    llm.generate.return_value = """
    {
        "decision": "RETRY",
        "context_relevance": 0.50,
        "faithfulness": 0.55,
        "answer_correctness": 0.60,
        "reason": "Both evidence sources need improvement.",
        "retry_target": "BOTH",
        "improved_query": "Re-evaluate department and access policy."
    }
    """

    result = agent.evaluate(
        query=(
            "What is my department and what does "
            "its access policy say?"
        ),
        answer="Incomplete answer.",
        chunks=[make_chunk()],
        database_result=(
            "user_id=7; department=Engineering"
        ),
    )

    assert result.decision == (
        CriticDecision.RETRY
    )

    assert result.retry_target == (
        RetryTarget.BOTH
    )

    assert result.improved_query == (
        "Re-evaluate department and access policy."
    )


# ======================================================================
# JSON parsing
# ======================================================================


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
        "retry_target": null,
        "improved_query": null
    }
    ```
    """

    result = agent.evaluate(
        query="test",
        answer="test",
        chunks=[make_chunk()],
    )

    assert result.decision == (
        CriticDecision.ACCEPT
    )


def test_invalid_json_is_rejected():

    agent, llm = make_agent()

    llm.generate.return_value = (
        "not valid json"
    )

    with pytest.raises(
        RuntimeError,
        match="invalid JSON",
    ):
        agent.evaluate(
            query="test",
            answer="test",
            chunks=[make_chunk()],
        )


def test_empty_llm_response_is_rejected():

    agent, llm = make_agent()

    llm.generate.return_value = ""

    with pytest.raises(
        RuntimeError,
        match="empty response",
    ):
        agent.evaluate(
            query="test",
            answer="test",
            chunks=[make_chunk()],
        )