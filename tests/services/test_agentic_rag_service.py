from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from app.dto.retrieved_chunk import RetrievedChunk
from app.services.agentic_rag_service import (
    AgenticRAGService,
)


def make_source():
    return RetrievedChunk(
        document_id=35,
        original_filename=(
            "02_organization_it_operations.pdf"
        ),
        chunk_id=1,
        chunk_index=0,
        chunk_text=(
            "Operators should check service health "
            "before making changes."
        ),
        token_count=20,
        metadata={
            "document_id": 35,
        },
        vector_score=0.90,
        rerank_score=0.90,
    )

def make_user():
    return SimpleNamespace(
        user_id=7,
        organization_id=2,
    )


def test_agentic_rag_returns_final_answer_and_sources():

    graph = Mock()

    graph.invoke.return_value = {
        "final_answer": "Final multi-agent answer.",
        "rag_result": SimpleNamespace(
            sources=[
                make_source(),
            ]
        ),
    }

    service = AgenticRAGService(
        graph=graph,
    )

    db = Mock()

    result = service.answer(
        db=db,
        query="  What is this?  ",
        current_user=make_user(),
    )

    assert result.query == "What is this?"

    assert result.answer == (
        "Final multi-agent answer."
    )

    assert len(result.sources) == 1

    assert result.sources[0].document_id == 35

    call = graph.invoke.call_args

    assert call.kwargs["context"]["db"] is db

    assert (
        call.kwargs["context"]["current_user"].user_id
        == 7
    )


def test_database_only_response_has_no_sources():

    graph = Mock()

    graph.invoke.return_value = {
        "final_answer": (
            "Your email is abhishek@example.com."
        ),
        "rag_result": None,
    }

    service = AgenticRAGService(
        graph=graph,
    )

    result = service.answer(
        db=Mock(),
        query="What is my email?",
        current_user=make_user(),
    )

    assert result.answer == (
        "Your email is abhishek@example.com."
    )

    assert result.sources == []


def test_empty_query_is_rejected():

    service = AgenticRAGService(
        graph=Mock(),
    )

    with pytest.raises(
        ValueError,
        match="Query cannot be empty",
    ):
        service.answer(
            db=Mock(),
            query="   ",
            current_user=make_user(),
        )


def test_missing_final_answer_is_rejected():

    graph = Mock()

    graph.invoke.return_value = {
        "final_answer": None,
        "rag_result": None,
    }

    service = AgenticRAGService(
        graph=graph,
    )

    with pytest.raises(
        RuntimeError,
        match="no final answer",
    ):
        service.answer(
            db=Mock(),
            query="test",
            current_user=make_user(),
        )


def test_max_retries_are_passed_to_graph():

    graph = Mock()

    graph.invoke.return_value = {
        "final_answer": "answer",
        "rag_result": None,
    }

    service = AgenticRAGService(
        graph=graph,
        max_retries=3,
    )

    service.answer(
        db=Mock(),
        query="test",
        current_user=make_user(),
    )

    initial_state = (
        graph.invoke.call_args.args[0]
    )

    assert initial_state["max_retries"] == 3