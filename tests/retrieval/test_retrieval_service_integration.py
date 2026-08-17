from __future__ import annotations

import pytest
from sqlalchemy import select

from app.database.database import SessionLocal
from app.models.document_chunks import DocumentChunk

from app.services.embedding.bge_m3_embedding_service import (
    BGEM3EmbeddingService,
)
from app.services.reranking.bge_reranker_service import (
    BGERerankerService,
)
from app.services.retrieval.retrieval_service import (
    RetrievalService,
)
from app.services.retrieval.vector_search_repository import (
    VectorSearchRepository,
)


# ======================================================================
# FIXTURES
# ======================================================================


@pytest.fixture
def db():
    """
    Real PostgreSQL/Supabase database session.

    Uses the same database setup as the existing
    embedding integration tests.
    """

    session = SessionLocal()

    try:
        yield session

    finally:
        session.rollback()
        session.close()


@pytest.fixture(scope="session")
def embedding_service():
    """
    Load BGE-M3 once for the entire pytest session.
    """

    return BGEM3EmbeddingService()


@pytest.fixture(scope="session")
def reranker_service():
    """
    Load BGE-Reranker-v2-M3 once for the entire pytest session.
    """

    return BGERerankerService(
        batch_size=8,
    )


@pytest.fixture(scope="session")
def vector_search_repository():
    """
    Real pgvector repository.
    """

    return VectorSearchRepository()


@pytest.fixture(scope="session")
def retrieval_service(
    embedding_service,
    vector_search_repository,
    reranker_service,
):
    """
    Real RetrievalService.

    Pipeline:

        BGE-M3
          ↓
        pgvector
          ↓
        BGE-Reranker
    """

    return RetrievalService(
        embedding_service=embedding_service,
        vector_search_repository=vector_search_repository,
        reranker_service=reranker_service,
        vector_top_k=30,
        rerank_top_k=5,
    )


# ======================================================================
# TEST USER
# ======================================================================


@pytest.fixture
def test_user():
    """
    Temporary authenticated user for the integration test.

    IMPORTANT:
    These ACL values must correspond to a user/document
    combination that exists in the database.
    """

    class TestUser:
        user_id = 9
        organization_id = 2
        team_id = 4
        department_id = 2
        role = "EMPLOYEE"

    return TestUser()


# ======================================================================
# REAL END-TO-END RETRIEVAL
# ======================================================================


def test_real_end_to_end_retrieval(
    db,
    retrieval_service,
    test_user,
):
    """
    Full real retrieval pipeline.

    User Query
        ↓
    BGE-M3
        ↓
    Query Embedding
        ↓
    pgvector
        ↓
    ACL filtering
        ↓
    Candidate chunks
        ↓
    BGE-Reranker-v2-M3
        ↓
    Final results
    """

    # ==================================================================
    # 1. Verify that embedded chunks exist
    # ==================================================================

    embedded_chunk = db.execute(
        select(DocumentChunk)
        .where(
            DocumentChunk.embedding.is_not(None)
        )
        .limit(1)
    ).scalar_one_or_none()

    if embedded_chunk is None:
        pytest.fail(
            "No embedded DocumentChunk rows exist. "
            "Run the embedding pipeline first."
        )

    # ==================================================================
    # 2. Query
    # ==================================================================

    query = (
        "What information is available "
        "in this document?"
    )

    # ==================================================================
    # 3. Execute complete retrieval pipeline
    # ==================================================================

    results = retrieval_service.retrieve(
        db=db,
        query=query,
        current_user=test_user,
    )

    # ==================================================================
    # 4. Basic result validation
    # ==================================================================

    assert isinstance(
        results,
        list,
    )

    assert results, (
        "Retrieval returned no results. "
        "This may indicate an ACL mismatch between "
        "the test user and the embedded documents."
    )

    # ==================================================================
    # 5. Result count
    # ==================================================================

    assert len(results) <= 5

    # ==================================================================
    # 6. Validate RetrievedChunk objects
    # ==================================================================

    for result in results:

        assert result.document_id is not None

        assert result.chunk_id is not None

        assert result.chunk_index is not None

        assert result.chunk_text

        assert result.vector_score is not None

        assert result.rerank_score is not None

        assert isinstance(
            result.vector_score,
            float,
        )

        assert isinstance(
            result.rerank_score,
            float,
        )

    # ==================================================================
    # 7. Verify reranking order
    # ==================================================================

    rerank_scores = [
        result.rerank_score
        for result in results
    ]

    assert rerank_scores == sorted(
        rerank_scores,
        reverse=True,
    )

    # ==================================================================
    # 8. Display actual retrieval results
    # ==================================================================

    print()
    print("=" * 80)
    print("REAL RETRIEVAL RESULTS")
    print("=" * 80)

    for rank, result in enumerate(
        results,
        start=1,
    ):

        print()
        print(f"Rank         : {rank}")
        print(
            f"Document ID  : "
            f"{result.document_id}"
        )
        print(
            f"Chunk ID     : "
            f"{result.chunk_id}"
        )
        print(
            f"Chunk Index  : "
            f"{result.chunk_index}"
        )
        print(
            f"Vector Score : "
            f"{result.vector_score:.6f}"
        )
        print(
            f"Rerank Score : "
            f"{result.rerank_score:.6f}"
        )
        print(
            f"Text         : "
            f"{result.chunk_text[:300]}"
        )

    print()
    print("=" * 80)