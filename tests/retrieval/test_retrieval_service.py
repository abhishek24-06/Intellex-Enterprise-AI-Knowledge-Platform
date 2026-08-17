from types import SimpleNamespace
from unittest.mock import Mock, ANY

import pytest

from app.dto.retrieved_chunk import RetrievedChunk
from app.services.retrieval.retrieval_service import (
    RetrievalService,
)


# ======================================================================
# Helpers
# ======================================================================


def make_chunk(
    chunk_id: int = 1,
    vector_score: float = 0.8,
):
    return RetrievedChunk(
        document_id=24,
        chunk_id=chunk_id,
        chunk_index=chunk_id,
        chunk_text=f"Chunk {chunk_id}",
        token_count=10,
        metadata={
            "document_id": 24,
        },
        vector_score=vector_score,
    )


def make_user():
    return SimpleNamespace(
        user_id=10,
        organization_id=1,
        team_id=5,
        department_id=3,
        role="EMPLOYEE",
    )


def make_service():

    embedding_service = Mock()

    vector_repository = Mock()

    reranker_service = Mock()

    service = RetrievalService(
        embedding_service=embedding_service,
        vector_search_repository=vector_repository,
        reranker_service=reranker_service,
    )

    return (
        service,
        embedding_service,
        vector_repository,
        reranker_service,
    )


# ======================================================================
# Constructor validation
# ======================================================================


def test_vector_top_k_must_be_positive():

    with pytest.raises(
        ValueError,
        match="vector_top_k",
    ):

        RetrievalService(
            embedding_service=Mock(),
            vector_search_repository=Mock(),
            reranker_service=Mock(),
            vector_top_k=0,
        )


def test_rerank_top_k_must_be_positive():

    with pytest.raises(
        ValueError,
        match="rerank_top_k",
    ):

        RetrievalService(
            embedding_service=Mock(),
            vector_search_repository=Mock(),
            reranker_service=Mock(),
            rerank_top_k=0,
        )


def test_rerank_top_k_cannot_exceed_vector_top_k():

    with pytest.raises(
        ValueError,
        match="rerank_top_k cannot be greater",
    ):

        RetrievalService(
            embedding_service=Mock(),
            vector_search_repository=Mock(),
            reranker_service=Mock(),
            vector_top_k=5,
            rerank_top_k=10,
        )


# ======================================================================
# Query validation
# ======================================================================


def test_empty_query_is_rejected():

    service, *_ = make_service()

    with pytest.raises(
        ValueError,
        match="Query cannot be empty",
    ):

        service.retrieve(
            db=Mock(),
            query="",
            current_user=make_user(),
        )


def test_whitespace_query_is_rejected():

    service, *_ = make_service()

    with pytest.raises(
        ValueError,
        match="Query cannot be empty",
    ):

        service.retrieve(
            db=Mock(),
            query="   ",
            current_user=make_user(),
        )


# ======================================================================
# Complete pipeline
# ======================================================================


def test_complete_retrieval_pipeline():

    (
        service,
        embedding_service,
        vector_repository,
        reranker_service,
    ) = make_service()

    embedding_service.embed_texts.return_value = [
        [0.1] * 1024
    ]

    candidates = [
        make_chunk(1),
        make_chunk(2),
        make_chunk(3),
    ]

    vector_repository.search.return_value = (
        candidates
    )

    final_results = [
        candidates[1],
        candidates[0],
    ]

    reranker_service.rerank.return_value = (
        final_results
    )

    db = Mock()

    user = make_user()

    result = service.retrieve(
        db=db,
        query="What is the leave policy?",
        current_user=user,
    )

    # --------------------------------------------------------------
    # Final result
    # --------------------------------------------------------------

    assert result == final_results

    # --------------------------------------------------------------
    # BGE-M3 called once
    # --------------------------------------------------------------

    embedding_service.embed_texts.assert_called_once_with(
        texts=[
            "What is the leave policy?"
        ]
    )

    # --------------------------------------------------------------
    # Vector search receives 1024 dimensions
    # --------------------------------------------------------------

    vector_repository.search.assert_called_once_with(
        db=db,
        query_embedding=[0.1] * 1024,
        current_user=user,
        top_k=30,
    )

    # --------------------------------------------------------------
    # Reranker receives SAME query
    # --------------------------------------------------------------

    reranker_service.rerank.assert_called_once_with(
        query="What is the leave policy?",
        chunks=candidates,
        top_k=5,
    )


# ======================================================================
# No candidates
# ======================================================================


def test_no_candidates_returns_empty_without_reranking():

    (
        service,
        embedding_service,
        vector_repository,
        reranker_service,
    ) = make_service()

    embedding_service.embed_texts.return_value = [
        [0.1] * 1024
    ]

    vector_repository.search.return_value = []

    result = service.retrieve(
        db=Mock(),
        query="What is the leave policy?",
        current_user=make_user(),
    )

    assert result == []

    reranker_service.rerank.assert_not_called()


# ======================================================================
# Fewer candidates than vector_top_k
# ======================================================================


def test_fewer_candidates_than_vector_top_k_is_valid():

    (
        service,
        embedding_service,
        vector_repository,
        reranker_service,
    ) = make_service()

    embedding_service.embed_texts.return_value = [
        [0.1] * 1024
    ]

    candidates = [
        make_chunk(1),
        make_chunk(2),
        make_chunk(3),
    ]

    vector_repository.search.return_value = (
        candidates
    )

    reranker_service.rerank.return_value = (
        candidates
    )

    result = service.retrieve(
        db=Mock(),
        query="test",
        current_user=make_user(),
    )

    assert len(result) == 3

    reranker_service.rerank.assert_called_once()


# ======================================================================
# Fewer candidates than rerank_top_k
# ======================================================================


def test_fewer_candidates_than_rerank_top_k_is_valid():

    (
        service,
        embedding_service,
        vector_repository,
        reranker_service,
    ) = make_service()

    embedding_service.embed_texts.return_value = [
        [0.1] * 1024
    ]

    candidates = [
        make_chunk(1),
        make_chunk(2),
    ]

    vector_repository.search.return_value = (
        candidates
    )

    reranker_service.rerank.return_value = (
        candidates
    )

    result = service.retrieve(
        db=Mock(),
        query="test",
        current_user=make_user(),
        vector_top_k=30,
        rerank_top_k=5,
    )

    assert len(result) == 2


# ======================================================================
# Per-request limits
# ======================================================================


def test_per_request_limits_override_defaults():

    (
        service,
        embedding_service,
        vector_repository,
        reranker_service,
    ) = make_service()

    embedding_service.embed_texts.return_value = [
        [0.1] * 1024
    ]

    candidates = [
        make_chunk(1),
        make_chunk(2),
    ]

    vector_repository.search.return_value = (
        candidates
    )

    reranker_service.rerank.return_value = (
        candidates
    )

    service.retrieve(
        db=Mock(),
        query="test",
        current_user=make_user(),
        vector_top_k=50,
        rerank_top_k=10,
    )

    vector_repository.search.assert_called_once_with(
        db=ANY,
        query_embedding=[0.1] * 1024,
        current_user=ANY,
        top_k=50,
    )

    reranker_service.rerank.assert_called_once_with(
        query="test",
        chunks=candidates,
        top_k=10,
    )


# ======================================================================
# Invalid per-request limits
# ======================================================================


def test_invalid_per_request_vector_top_k():

    service, *_ = make_service()

    with pytest.raises(
        ValueError,
        match="vector_top_k",
    ):

        service.retrieve(
            db=Mock(),
            query="test",
            current_user=make_user(),
            vector_top_k=0,
        )


def test_invalid_per_request_rerank_top_k():

    service, *_ = make_service()

    with pytest.raises(
        ValueError,
        match="rerank_top_k",
    ):

        service.retrieve(
            db=Mock(),
            query="test",
            current_user=make_user(),
            rerank_top_k=0,
        )


def test_per_request_rerank_limit_cannot_exceed_vector_limit():

    service, *_ = make_service()

    with pytest.raises(
        ValueError,
        match="rerank_top_k cannot be greater",
    ):

        service.retrieve(
            db=Mock(),
            query="test",
            current_user=make_user(),
            vector_top_k=5,
            rerank_top_k=10,
        )


# ======================================================================
# Embedding count validation
# ======================================================================


def test_embedding_service_must_return_one_embedding():

    (
        service,
        embedding_service,
        _,
        _,
    ) = make_service()

    embedding_service.embed_texts.return_value = []

    with pytest.raises(
        RuntimeError,
        match="unexpected number of embeddings",
    ):

        service.retrieve(
            db=Mock(),
            query="test",
            current_user=make_user(),
        )


# ======================================================================
# Embedding dimension validation
# ======================================================================


def test_query_embedding_must_have_1024_dimensions():

    (
        service,
        embedding_service,
        _,
        _,
    ) = make_service()

    embedding_service.embed_texts.return_value = [
        [0.1] * 1023
    ]

    with pytest.raises(
        RuntimeError,
        match="1024 dimensions",
    ):

        service.retrieve(
            db=Mock(),
            query="test",
            current_user=make_user(),
        )