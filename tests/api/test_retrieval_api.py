from dataclasses import dataclass
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.dependencies.auth import get_current_user
from app.database.database import get_db
from app.api.retrieval import retrieval_service


# ======================================================================
# TEST USER
# ======================================================================


@dataclass
class TestUser:
    user_id: int = 9
    organization_id: int = 2
    department_id: int = 2
    team_id: int = 4
    is_active: bool = True


# ======================================================================
# FIXTURES
# ======================================================================


@pytest.fixture
def test_user():
    return TestUser()


@pytest.fixture
def mock_db():
    return Mock()


@pytest.fixture
def mock_retrieval_service():
    return Mock()


@pytest.fixture
def client(test_user, mock_db, mock_retrieval_service):

    def override_get_current_user():
        return test_user

    def override_get_db():
        yield mock_db

    app.dependency_overrides[
        get_current_user
    ] = override_get_current_user

    app.dependency_overrides[
        get_db
    ] = override_get_db

    original_service = retrieval_service

    # Replace the module-level retrieval service used by the endpoint.
    import app.api.retrieval as retrieval_api

    retrieval_api.retrieval_service = mock_retrieval_service

    client = TestClient(app)

    yield client

    app.dependency_overrides.clear()

    retrieval_api.retrieval_service = original_service


# ======================================================================
# HELPERS
# ======================================================================


def make_retrieved_chunk(
    *,
    document_id: int = 24,
    chunk_id: int = 100,
    chunk_index: int = 0,
):
    from app.dto.retrieved_chunk import RetrievedChunk

    return RetrievedChunk(
        document_id=document_id,
        chunk_id=chunk_id,
        chunk_index=chunk_index,
        chunk_text="This is a retrieved test chunk.",
        token_count=10,
        metadata={
            "document_id": document_id,
            "test": True,
        },
        vector_score=0.75,
        rerank_score=2.50,
    )


# ======================================================================
# TEST 1
# ======================================================================


def test_authenticated_retrieval_request_returns_results(
    client,
    mock_retrieval_service,
    mock_db,
    test_user,
):

    chunk = make_retrieved_chunk()

    mock_retrieval_service.retrieve.return_value = [
        chunk
    ]

    response = client.post(
        "/retrieval/search",
        json={
            "query": "What is the leave policy?"
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["query"] == "What is the leave policy?"

    assert len(data["results"]) == 1

    result = data["results"][0]

    assert result["document_id"] == 24
    assert result["chunk_id"] == 100
    assert result["chunk_index"] == 0
    assert result["chunk_text"] == (
        "This is a retrieved test chunk."
    )
    assert result["token_count"] == 10
    assert result["vector_score"] == 0.75
    assert result["rerank_score"] == 2.50


# ======================================================================
# TEST 2
# ======================================================================


def test_authenticated_request_passes_current_user_to_service(
    client,
    mock_retrieval_service,
    mock_db,
    test_user,
):

    mock_retrieval_service.retrieve.return_value = []

    response = client.post(
        "/retrieval/search",
        json={
            "query": "Tell me about deepfake detection."
        },
    )

    assert response.status_code == 200

    mock_retrieval_service.retrieve.assert_called_once_with(
        db=mock_db,
        query="Tell me about deepfake detection.",
        current_user=test_user,
    )


# ======================================================================
# TEST 3
# ======================================================================


def test_empty_query_is_rejected(
    client,
    mock_retrieval_service,
):

    response = client.post(
        "/retrieval/search",
        json={
            "query": ""
        },
    )

    assert response.status_code == 422

    mock_retrieval_service.retrieve.assert_not_called()


# ======================================================================
# TEST 4
# ======================================================================


def test_whitespace_query_is_rejected(
    client,
    mock_retrieval_service,
):

    response = client.post(
        "/retrieval/search",
        json={
            "query": "     "
        },
    )

    assert response.status_code == 422

    mock_retrieval_service.retrieve.assert_not_called()


# ======================================================================
# TEST 5
# ======================================================================


def test_missing_query_is_rejected(
    client,
    mock_retrieval_service,
):

    response = client.post(
        "/retrieval/search",
        json={}
    )

    assert response.status_code == 422

    mock_retrieval_service.retrieve.assert_not_called()


# ======================================================================
# TEST 6
# ======================================================================


def test_no_results_returns_empty_results(
    client,
    mock_retrieval_service,
):

    mock_retrieval_service.retrieve.return_value = []

    response = client.post(
        "/retrieval/search",
        json={
            "query": "Something that has no results."
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["query"] == (
        "Something that has no results."
    )

    assert data["results"] == []


# ======================================================================
# TEST 7
# ======================================================================


def test_rerank_score_can_be_null(
    client,
    mock_retrieval_service,
):

    chunk = make_retrieved_chunk()

    chunk.rerank_score = None

    mock_retrieval_service.retrieve.return_value = [
        chunk
    ]

    response = client.post(
        "/retrieval/search",
        json={
            "query": "Test query"
        },
    )

    assert response.status_code == 200

    result = response.json()["results"][0]

    assert result["rerank_score"] is None


# ======================================================================
# TEST 8
# ======================================================================


def test_top_k_parameters_are_not_required(
    client,
    mock_retrieval_service,
):

    mock_retrieval_service.retrieve.return_value = []

    response = client.post(
        "/retrieval/search",
        json={
            "query": "What is the company policy?"
        },
    )

    assert response.status_code == 200

    mock_retrieval_service.retrieve.assert_called_once()