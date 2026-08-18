from dataclasses import dataclass
from datetime import UTC, datetime
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.dependencies.auth import get_current_user
from app.database.database import get_db


@dataclass
class TestUser:
    user_id: int = 1
    organization_id: int = 2
    is_active: bool = True


def make_session(
    *,
    session_id: int = 10,
    user_id: int = 1,
    title: str | None = "Test Session",
    is_pinned: bool = False,
):
    session = Mock()

    session.session_id = session_id
    session.user_id = user_id
    session.title = title
    session.created_at = datetime.now(UTC)
    session.last_active = datetime.now(UTC)
    session.is_pinned = is_pinned

    return session


@pytest.fixture
def test_user():
    return TestUser()


@pytest.fixture
def db():
    return Mock()


@pytest.fixture
def client(test_user, db):

    def override_current_user():
        return test_user

    def override_db():
        yield db

    app.dependency_overrides[
        get_current_user
    ] = override_current_user

    app.dependency_overrides[
        get_db
    ] = override_db

    client = TestClient(app)

    yield client

    app.dependency_overrides.clear()


def test_create_chat_session(
    client,
    db,
    test_user,
    monkeypatch,
):

    session = make_session(
        session_id=42,
        user_id=test_user.user_id,
        title="Deepfake Research",
    )

    import app.api.chat_sessions as module

    monkeypatch.setattr(
        module,
        "create_chat_session",
        lambda **kwargs: session,
    )

    response = client.post(
        "/chat/sessions",
        json={
            "title": "Deepfake Research"
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["session_id"] == 42
    assert data["title"] == "Deepfake Research"
    assert data["is_pinned"] is False


def test_create_session_without_title(
    client,
    monkeypatch,
):

    session = make_session(
        session_id=43,
        title=None,
    )

    import app.api.chat_sessions as module

    monkeypatch.setattr(
        module,
        "create_chat_session",
        lambda **kwargs: session,
    )

    response = client.post(
        "/chat/sessions",
        json={},
    )

    assert response.status_code == 201

    assert response.json()["title"] is None


def test_empty_title_becomes_none(
    client,
    monkeypatch,
):

    session = make_session(
        session_id=44,
        title=None,
    )

    import app.api.chat_sessions as module

    def fake_create(**kwargs):
        assert kwargs["title"] is None
        return session

    monkeypatch.setattr(
        module,
        "create_chat_session",
        fake_create,
    )

    response = client.post(
        "/chat/sessions",
        json={
            "title": "   ",
        },
    )

    assert response.status_code == 201


def test_list_sessions(
    client,
    monkeypatch,
):

    sessions = [
        make_session(
            session_id=1,
            title="First",
        ),
        make_session(
            session_id=2,
            title="Second",
            is_pinned=True,
        ),
    ]

    import app.api.chat_sessions as module

    monkeypatch.setattr(
        module,
        "get_user_chat_sessions",
        lambda **kwargs: sessions,
    )

    response = client.get(
        "/chat/sessions"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data["sessions"]) == 2
    assert data["sessions"][0]["session_id"] == 1
    assert data["sessions"][1]["session_id"] == 2


def test_get_session(
    client,
    monkeypatch,
):

    session = make_session(
        session_id=50,
        title="My Session",
    )

    import app.api.chat_sessions as module

    monkeypatch.setattr(
        module,
        "get_chat_session",
        lambda **kwargs: session,
    )

    response = client.get(
        "/chat/sessions/50"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["session_id"] == 50
    assert data["title"] == "My Session"


def test_get_missing_session_returns_404(
    client,
    monkeypatch,
):

    import app.api.chat_sessions as module

    monkeypatch.setattr(
        module,
        "get_chat_session",
        lambda **kwargs: None,
    )

    response = client.get(
        "/chat/sessions/999"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Chat session not found."
    )


def test_delete_session(
    client,
    monkeypatch,
):

    import app.api.chat_sessions as module

    monkeypatch.setattr(
        module,
        "delete_chat_session",
        lambda **kwargs: True,
    )

    response = client.delete(
        "/chat/sessions/42"
    )

    assert response.status_code == 204


def test_delete_missing_session_returns_404(
    client,
    monkeypatch,
):

    import app.api.chat_sessions as module

    monkeypatch.setattr(
        module,
        "delete_chat_session",
        lambda **kwargs: False,
    )

    response = client.delete(
        "/chat/sessions/999"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "Chat session not found."
    )