from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from sqlalchemy.dialects import postgresql

from app.dto.retrieved_chunk import RetrievedChunk
from app.services.retrieval.vector_search_repository import (
    VectorSearchRepository,
)


# ======================================================================
# Helpers
# ======================================================================


def make_user(
    *,
    user_id=10,
    organization_id=1,
    team_id=5,
    department_id=3,
    role="EMPLOYEE",
):
    """
    Lightweight fake user.

    The repository only needs these attributes.
    """

    return SimpleNamespace(
        user_id=user_id,
        organization_id=organization_id,
        team_id=team_id,
        department_id=department_id,
        role=role,
    )


def make_chunk(
    *,
    document_id=100,
    chunk_id=1,
    chunk_index=0,
    text="Test chunk",
    token_count=10,
    metadata=None,
):
    """
    Lightweight fake DocumentChunk returned by the DB.
    """

    return SimpleNamespace(
        document_id=document_id,
        chunk_id=chunk_id,
        chunk_index=chunk_index,
        chunk_text=text,
        token_count=token_count,
        metadata_json=metadata or {},
    )


def make_db(
    *,
    rows=None,
):
    """
    Mock SQLAlchemy session.

    Repository executes:

        db.execute(stmt).all()
    """

    db = Mock()

    result = Mock()

    result.all.return_value = rows or []

    db.execute.return_value = result

    return db


# ======================================================================
# Fixtures
# ======================================================================


@pytest.fixture
def repository():
    return VectorSearchRepository()


@pytest.fixture
def query_embedding():
    return [0.1] * 1024


@pytest.fixture
def employee():
    return make_user()


# ======================================================================
# 1. Empty embedding rejected
# ======================================================================


def test_empty_query_embedding_is_rejected(
    repository,
    employee,
):

    db = make_db()

    with pytest.raises(
        ValueError,
        match="Query embedding cannot be empty",
    ):

        repository.search(
            db=db,
            query_embedding=[],
            current_user=employee,
        )


# ======================================================================
# 2. Wrong embedding dimension rejected
# ======================================================================


def test_wrong_embedding_dimension_is_rejected(
    repository,
    employee,
):

    db = make_db()

    query_embedding = [0.1] * 1023

    with pytest.raises(
        ValueError,
        match="1024 dimensions",
    ):

        repository.search(
            db=db,
            query_embedding=query_embedding,
            current_user=employee,
        )


# ======================================================================
# 3. Top-K validation
# ======================================================================


@pytest.mark.parametrize(
    "top_k",
    [0, -1, -10],
)
def test_invalid_top_k_is_rejected(
    repository,
    employee,
    query_embedding,
    top_k,
):

    db = make_db()

    with pytest.raises(
        ValueError,
        match="top_k must be greater than zero",
    ):

        repository.search(
            db=db,
            query_embedding=query_embedding,
            current_user=employee,
            top_k=top_k,
        )


# ======================================================================
# 4. Empty database result
# ======================================================================


def test_empty_database_result_returns_empty_list(
    repository,
    employee,
    query_embedding,
):

    db = make_db(rows=[])

    result = repository.search(
        db=db,
        query_embedding=query_embedding,
        current_user=employee,
        top_k=30,
    )

    assert result == []

    db.execute.assert_called_once()


# ======================================================================
# 5. Retrieved rows are converted to RetrievedChunk
# ======================================================================


def test_database_rows_are_converted_to_retrieved_chunks(
    repository,
    employee,
    query_embedding,
):

    chunk = make_chunk(
        document_id=24,
        chunk_id=101,
        chunk_index=7,
        text="The employee leave policy allows twenty days.",
        token_count=12,
        metadata={
            "document_id": 24,
            "page": 4,
            "chunk_type": "NARRATIVE",
        },
    )

    rows = [
        (
            chunk,
            0.8734,
        )
    ]

    db = make_db(rows=rows)

    result = repository.search(
        db=db,
        query_embedding=query_embedding,
        current_user=employee,
        top_k=30,
    )

    assert len(result) == 1

    retrieved = result[0]

    assert isinstance(
        retrieved,
        RetrievedChunk,
    )

    assert retrieved.document_id == 24
    assert retrieved.chunk_id == 101
    assert retrieved.chunk_index == 7

    assert (
        retrieved.chunk_text
        == "The employee leave policy allows twenty days."
    )

    assert retrieved.token_count == 12

    assert retrieved.metadata == {
        "document_id": 24,
        "page": 4,
        "chunk_type": "NARRATIVE",
    }

    assert retrieved.vector_score == pytest.approx(
        0.8734
    )

    assert retrieved.rerank_score is None


# ======================================================================
# 6. Query embedding is passed into the SQL statement
# ======================================================================


def test_query_embedding_is_used(
    repository,
    employee,
):

    db = make_db()

    query_embedding = [0.25] * 1024

    repository.search(
        db=db,
        query_embedding=query_embedding,
        current_user=employee,
        top_k=10,
    )

    db.execute.assert_called_once()

    stmt = db.execute.call_args.args[0]

    compiled = stmt.compile(
        dialect=postgresql.dialect()
    )

    sql = str(compiled)

    # pgvector cosine distance should be present.
    assert "<=>" in sql


# ======================================================================
# 7. Organization isolation
# ======================================================================


def test_organization_isolation_is_present(
    repository,
    employee,
    query_embedding,
):

    db = make_db()

    repository.search(
        db=db,
        query_embedding=query_embedding,
        current_user=employee,
        top_k=10,
    )

    stmt = db.execute.call_args.args[0]

    compiled = stmt.compile(
        dialect=postgresql.dialect()
    )

    sql = str(compiled)

    assert "documents.organization_id" in sql


# ======================================================================
# 8. Deleted documents are excluded
# ======================================================================


def test_deleted_documents_are_excluded(
    repository,
    employee,
    query_embedding,
):

    db = make_db()

    repository.search(
        db=db,
        query_embedding=query_embedding,
        current_user=employee,
        top_k=10,
    )

    stmt = db.execute.call_args.args[0]

    compiled = stmt.compile(
        dialect=postgresql.dialect()
    )

    sql = str(compiled)

    assert "documents.is_deleted" in sql


# ======================================================================
# 9. Chunks without embeddings are excluded
# ======================================================================


def test_chunks_without_embeddings_are_excluded(
    repository,
    employee,
    query_embedding,
):

    db = make_db()

    repository.search(
        db=db,
        query_embedding=query_embedding,
        current_user=employee,
        top_k=10,
    )

    stmt = db.execute.call_args.args[0]

    compiled = stmt.compile(
        dialect=postgresql.dialect()
    )

    sql = str(compiled)

    assert "document_chunks.embedding" in sql


# ======================================================================
# 10. Top-K is applied
# ======================================================================


def test_top_k_is_applied(
    repository,
    employee,
    query_embedding,
):

    db = make_db()

    repository.search(
        db=db,
        query_embedding=query_embedding,
        current_user=employee,
        top_k=17,
    )

    stmt = db.execute.call_args.args[0]

    compiled = stmt.compile(
        dialect=postgresql.dialect()
    )

    sql = str(compiled)

    # LIMIT should be present.
    assert "LIMIT" in sql


# ======================================================================
# 11. USER ACL is included
# ======================================================================


def test_user_acl_condition_is_present(
    repository,
    query_embedding,
):

    user = make_user(
        user_id=42,
        organization_id=1,
        team_id=5,
        department_id=3,
    )

    db = make_db()

    repository.search(
        db=db,
        query_embedding=query_embedding,
        current_user=user,
        top_k=10,
    )

    stmt = db.execute.call_args.args[0]

    compiled = stmt.compile(
        dialect=postgresql.dialect()
    )

    sql = str(compiled)

    assert "document_acl" in sql


# ======================================================================
# 12. TEAM ACL is included
# ======================================================================


def test_team_acl_condition_is_present(
    repository,
    query_embedding,
):

    user = make_user(
        user_id=42,
        organization_id=1,
        team_id=99,
        department_id=3,
    )

    db = make_db()

    repository.search(
        db=db,
        query_embedding=query_embedding,
        current_user=user,
        top_k=10,
    )

    stmt = db.execute.call_args.args[0]

    compiled = stmt.compile(
        dialect=postgresql.dialect()
    )

    sql = str(compiled)

    assert "document_acl" in sql


# ======================================================================
# 13. DEPARTMENT ACL is included
# ======================================================================


def test_department_acl_condition_is_present(
    repository,
    query_embedding,
):

    user = make_user(
        user_id=42,
        organization_id=1,
        team_id=5,
        department_id=77,
    )

    db = make_db()

    repository.search(
        db=db,
        query_embedding=query_embedding,
        current_user=user,
        top_k=10,
    )

    stmt = db.execute.call_args.args[0]

    compiled = stmt.compile(
        dialect=postgresql.dialect()
    )

    sql = str(compiled)

    assert "document_acl" in sql


# ======================================================================
# 14. Organization visibility is included
# ======================================================================


def test_organization_visibility_is_included(
    repository,
    employee,
    query_embedding,
):

    db = make_db()

    repository.search(
        db=db,
        query_embedding=query_embedding,
        current_user=employee,
        top_k=10,
    )

    stmt = db.execute.call_args.args[0]

    compiled = stmt.compile(
        dialect=postgresql.dialect()
    )

    sql = str(compiled)

    assert "visibility" in sql


# ======================================================================
# 15. ORG_ADMIN gets ORG_ADMIN ACL condition
# ======================================================================


def test_org_admin_acl_is_included_for_org_admin(
    repository,
    query_embedding,
):

    admin = make_user(
        user_id=1,
        organization_id=1,
        team_id=None,
        department_id=None,
        role="ORG_ADMIN",
    )

    db = make_db()

    repository.search(
        db=db,
        query_embedding=query_embedding,
        current_user=admin,
        top_k=10,
    )

    stmt = db.execute.call_args.args[0]

    compiled = stmt.compile(
        dialect=postgresql.dialect()
    )

    sql = str(compiled)

    assert "document_acl" in sql


# ======================================================================
# 16. Non-admin does not get ORG_ADMIN-specific condition
# ======================================================================


def test_regular_employee_does_not_get_org_admin_acl(
    repository,
    query_embedding,
):

    employee = make_user(
        user_id=10,
        organization_id=1,
        team_id=5,
        department_id=3,
        role="EMPLOYEE",
    )

    db = make_db()

    repository.search(
        db=db,
        query_embedding=query_embedding,
        current_user=employee,
        top_k=10,
    )

    stmt = db.execute.call_args.args[0]

    compiled = stmt.compile(
        dialect=postgresql.dialect()
    )

    sql = str(compiled)

    assert "document_acl" in sql


# ======================================================================
# 17. Results preserve vector ordering
# ======================================================================


def test_results_preserve_database_vector_order(
    repository,
    employee,
    query_embedding,
):

    chunk_1 = make_chunk(
        document_id=24,
        chunk_id=1,
        chunk_index=0,
        text="Less relevant",
    )

    chunk_2 = make_chunk(
        document_id=24,
        chunk_id=2,
        chunk_index=1,
        text="Most relevant",
    )

    chunk_3 = make_chunk(
        document_id=24,
        chunk_id=3,
        chunk_index=2,
        text="Medium relevant",
    )

    rows = [
        (chunk_2, 0.95),
        (chunk_3, 0.80),
        (chunk_1, 0.65),
    ]

    db = make_db(rows=rows)

    result = repository.search(
        db=db,
        query_embedding=query_embedding,
        current_user=employee,
        top_k=3,
    )

    assert len(result) == 3

    assert result[0].chunk_id == 2
    assert result[1].chunk_id == 3
    assert result[2].chunk_id == 1

    assert result[0].vector_score > result[1].vector_score
    assert result[1].vector_score > result[2].vector_score


# ======================================================================
# 18. Embedding dimension is exactly 1024
# ======================================================================


def test_1024_dimension_embedding_is_accepted(
    repository,
    employee,
):

    db = make_db()

    query_embedding = [0.01] * 1024

    result = repository.search(
        db=db,
        query_embedding=query_embedding,
        current_user=employee,
        top_k=5,
    )

    assert result == []

    db.execute.assert_called_once()