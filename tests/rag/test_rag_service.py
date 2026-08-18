from unittest.mock import Mock

import pytest

from app.dto.rag_response import RAGResult
from app.dto.retrieved_chunk import RetrievedChunk
from app.services.rag.rag_service import RAGService


# ======================================================================
# HELPERS
# ======================================================================


def make_chunk(
    *,
    document_id: int = 24,
    original_filename: str = "deepfake_detection.pdf",
    chunk_id: int = 100,
    chunk_index: int = 0,
    text: str = "Deepfake detection uses CNNs.",
):
    return RetrievedChunk(
        document_id=document_id,
        original_filename=original_filename,
        chunk_id=chunk_id,
        chunk_index=chunk_index,
        chunk_text=text,
        token_count=10,
        metadata={
            "document_id": document_id,
        },
        vector_score=0.8,
        rerank_score=2.5,
    )


def make_service():

    retrieval_service = Mock()

    answer_generation_service = Mock()

    answer_generation_service.generate.return_value = (
        "The deepfake detection system uses CNNs."
    )

    service = RAGService(
        retrieval_service=retrieval_service,
        answer_generation_service=answer_generation_service,
    )

    return (
        service,
        retrieval_service,
        answer_generation_service,
    )


# ======================================================================
# QUERY VALIDATION
# ======================================================================


def test_empty_query_is_rejected():

    service, _, _ = make_service()

    with pytest.raises(
        ValueError,
        match="Query cannot be empty",
    ):
        service.answer(
            db=Mock(),
            query="",
            current_user=Mock(),
        )


def test_whitespace_query_is_rejected():

    service, _, _ = make_service()

    with pytest.raises(
        ValueError,
        match="Query cannot be empty",
    ):
        service.answer(
            db=Mock(),
            query="   ",
            current_user=Mock(),
        )


# ======================================================================
# RETRIEVAL
# ======================================================================


def test_query_is_normalized_before_retrieval():

    (
        service,
        retrieval_service,
        _,
    ) = make_service()

    chunks = [make_chunk()]

    retrieval_service.retrieve.return_value = chunks

    db = Mock()
    user = Mock()

    service.answer(
        db=db,
        query="   What is deepfake detection?   ",
        current_user=user,
    )

    retrieval_service.retrieve.assert_called_once_with(
        db=db,
        query="What is deepfake detection?",
        current_user=user,
    )


def test_retrieved_chunks_are_passed_to_generation():

    (
        service,
        retrieval_service,
        generation_service,
    ) = make_service()

    chunks = [
        make_chunk(
            document_id=24,
            original_filename="deepfake.pdf",
            chunk_id=100,
        ),
        make_chunk(
            document_id=28,
            original_filename="project.docx",
            chunk_id=200,
        ),
    ]

    retrieval_service.retrieve.return_value = chunks

    service.answer(
        db=Mock(),
        query="What is deepfake detection?",
        current_user=Mock(),
    )

    generation_service.generate.assert_called_once_with(
        query="What is deepfake detection?",
        chunks=chunks,
    )


# ======================================================================
# FINAL RESULT
# ======================================================================


def test_generated_answer_and_sources_are_returned():

    (
        service,
        retrieval_service,
        generation_service,
    ) = make_service()

    chunks = [
        make_chunk(
            document_id=24,
            original_filename="deepfake.pdf",
            chunk_id=100,
        ),
        make_chunk(
            document_id=28,
            original_filename="research.docx",
            chunk_id=200,
        ),
    ]

    retrieval_service.retrieve.return_value = chunks

    result = service.answer(
        db=Mock(),
        query="What is deepfake detection?",
        current_user=Mock(),
    )

    assert isinstance(
        result,
        RAGResult,
    )

    assert result.query == (
        "What is deepfake detection?"
    )

    assert result.answer == (
        "The deepfake detection system uses CNNs."
    )

    assert result.sources == chunks


# ======================================================================
# NO RETRIEVED CONTEXT
# ======================================================================


def test_no_retrieved_chunks_returns_fallback_answer():

    (
        service,
        retrieval_service,
        generation_service,
    ) = make_service()

    retrieval_service.retrieve.return_value = []

    result = service.answer(
        db=Mock(),
        query="Question with no available context.",
        current_user=Mock(),
    )

    assert result.query == (
        "Question with no available context."
    )

    assert result.answer == (
        "I could not find enough information "
        "in the available knowledge base to "
        "answer this question."
    )

    assert result.sources == []

    generation_service.generate.assert_not_called()


# ======================================================================
# SECURITY / PIPELINE BEHAVIOR
# ======================================================================


def test_generation_is_never_called_when_retrieval_returns_nothing():

    (
        service,
        retrieval_service,
        generation_service,
    ) = make_service()

    retrieval_service.retrieve.return_value = []

    service.answer(
        db=Mock(),
        query="What is this?",
        current_user=Mock(),
    )

    generation_service.generate.assert_not_called()


def test_retrieval_failure_propagates_and_generation_is_not_called():

    (
        service,
        retrieval_service,
        generation_service,
    ) = make_service()

    retrieval_service.retrieve.side_effect = (
        RuntimeError("Retrieval failed")
    )

    with pytest.raises(
        RuntimeError,
        match="Retrieval failed",
    ):
        service.answer(
            db=Mock(),
            query="Test query",
            current_user=Mock(),
        )

    generation_service.generate.assert_not_called()


def test_generation_failure_propagates():

    (
        service,
        retrieval_service,
        generation_service,
    ) = make_service()

    retrieval_service.retrieve.return_value = [
        make_chunk()
    ]

    generation_service.generate.side_effect = (
        RuntimeError("Generation failed")
    )

    with pytest.raises(
        RuntimeError,
        match="Generation failed",
    ):
        service.answer(
            db=Mock(),
            query="Test query",
            current_user=Mock(),
        )