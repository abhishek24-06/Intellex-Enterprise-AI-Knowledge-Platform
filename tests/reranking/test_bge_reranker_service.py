from unittest.mock import Mock

import pytest

from app.dto.retrieved_chunk import RetrievedChunk
from app.services.reranking.bge_reranker_service import (
    BGERerankerService,
)


# ======================================================================
# Helpers
# ======================================================================


def make_chunk(
    *,
    chunk_id: int,
    text: str,
    vector_score: float = 0.5,
):
    return RetrievedChunk(
        document_id=24,
        chunk_id=chunk_id,
        chunk_index=chunk_id,
        chunk_text=text,
        token_count=10,
        metadata={
            "document_id": 24,
        },
        vector_score=vector_score,
    )


def make_service():
    """
    Create the service without loading the actual Hugging Face model.

    Unit tests should be fast and deterministic.
    """

    service = BGERerankerService.__new__(
        BGERerankerService
    )

    service.model_name = (
        BGERerankerService.MODEL_NAME
    )

    service.batch_size = 8

    service.device = "cpu"

    service.tokenizer = Mock()

    service.model = Mock()

    return service


# ======================================================================
# Empty input
# ======================================================================


def test_empty_chunks_returns_empty_list():

    service = make_service()

    result = service.rerank(
        query="What is the leave policy?",
        chunks=[],
    )

    assert result == []


# ======================================================================
# Empty query
# ======================================================================


def test_empty_query_is_rejected():

    service = make_service()

    chunks = [
        make_chunk(
            chunk_id=1,
            text="Leave policy",
        )
    ]

    with pytest.raises(
        ValueError,
        match="Query cannot be empty",
    ):

        service.rerank(
            query="",
            chunks=chunks,
        )


# ======================================================================
# Whitespace query
# ======================================================================


def test_whitespace_query_is_rejected():

    service = make_service()

    chunks = [
        make_chunk(
            chunk_id=1,
            text="Leave policy",
        )
    ]

    with pytest.raises(
        ValueError,
        match="Query cannot be empty",
    ):

        service.rerank(
            query="   ",
            chunks=chunks,
        )


# ======================================================================
# Invalid top_k
# ======================================================================


def test_invalid_top_k_is_rejected():

    service = make_service()

    chunks = [
        make_chunk(
            chunk_id=1,
            text="Leave policy",
        )
    ]

    with pytest.raises(
        ValueError,
        match="top_k must be greater than zero",
    ):

        service.rerank(
            query="What is the leave policy?",
            chunks=chunks,
            top_k=0,
        )


# ======================================================================
# Reranking order
# ======================================================================


def test_chunks_are_sorted_by_rerank_score():

    service = make_service()

    chunks = [
        make_chunk(
            chunk_id=1,
            text="Chunk one",
        ),
        make_chunk(
            chunk_id=2,
            text="Chunk two",
        ),
        make_chunk(
            chunk_id=3,
            text="Chunk three",
        ),
    ]

    service._score_pairs = Mock(
        return_value=[
            0.20,
            0.95,
            0.70,
        ]
    )

    result = service.rerank(
        query="What is relevant?",
        chunks=chunks,
    )

    assert [
        chunk.chunk_id
        for chunk in result
    ] == [
        2,
        3,
        1,
    ]

    assert result[0].rerank_score == pytest.approx(
        0.95
    )

    assert result[1].rerank_score == pytest.approx(
        0.70
    )

    assert result[2].rerank_score == pytest.approx(
        0.20
    )


# ======================================================================
# Top-K
# ======================================================================


def test_top_k_returns_only_requested_number():

    service = make_service()

    chunks = [
        make_chunk(
            chunk_id=1,
            text="Chunk one",
        ),
        make_chunk(
            chunk_id=2,
            text="Chunk two",
        ),
        make_chunk(
            chunk_id=3,
            text="Chunk three",
        ),
        make_chunk(
            chunk_id=4,
            text="Chunk four",
        ),
    ]

    service._score_pairs = Mock(
        return_value=[
            0.20,
            0.95,
            0.70,
            0.80,
        ]
    )

    result = service.rerank(
        query="What is relevant?",
        chunks=chunks,
        top_k=2,
    )

    assert len(result) == 2

    assert [
        chunk.chunk_id
        for chunk in result
    ] == [
        2,
        4,
    ]


# ======================================================================
# Scores are attached to original chunks
# ======================================================================


def test_scores_are_attached_to_chunks():

    service = make_service()

    chunks = [
        make_chunk(
            chunk_id=10,
            text="First",
        ),
        make_chunk(
            chunk_id=20,
            text="Second",
        ),
    ]

    service._score_pairs = Mock(
        return_value=[
            0.31,
            0.88,
        ]
    )

    result = service.rerank(
        query="test",
        chunks=chunks,
    )

    by_id = {
        chunk.chunk_id: chunk
        for chunk in result
    }

    assert by_id[10].rerank_score == pytest.approx(
        0.31
    )

    assert by_id[20].rerank_score == pytest.approx(
        0.88
    )


# ======================================================================
# Scoring receives query/chunk pairs
# ======================================================================


def test_query_and_chunk_text_are_passed_to_scorer():

    service = make_service()

    chunks = [
        make_chunk(
            chunk_id=1,
            text="First chunk",
        ),
        make_chunk(
            chunk_id=2,
            text="Second chunk",
        ),
    ]

    service._score_pairs = Mock(
        return_value=[
            0.5,
            0.7,
        ]
    )

    service.rerank(
        query="What is the policy?",
        chunks=chunks,
    )

    service._score_pairs.assert_called_once_with(
        [
            (
                "What is the policy?",
                "First chunk",
            ),
            (
                "What is the policy?",
                "Second chunk",
            ),
        ]
    )


# ======================================================================
# top_k=None returns all chunks
# ======================================================================


def test_none_top_k_returns_all_chunks():

    service = make_service()

    chunks = [
        make_chunk(
            chunk_id=1,
            text="First",
        ),
        make_chunk(
            chunk_id=2,
            text="Second",
        ),
        make_chunk(
            chunk_id=3,
            text="Third",
        ),
    ]

    service._score_pairs = Mock(
        return_value=[
            0.4,
            0.9,
            0.6,
        ]
    )

    result = service.rerank(
        query="test",
        chunks=chunks,
        top_k=None,
    )

    assert len(result) == 3