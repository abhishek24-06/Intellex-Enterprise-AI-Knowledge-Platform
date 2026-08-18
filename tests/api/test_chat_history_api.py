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


def make_chat(
    *,
    chat_id: int,
    session_id: int,
    question: str,
    answer: str,
    feedback=None,
):

    chat = Mock()

    chat.chat_id = chat_id
    chat.session_id = session_id
    chat.question = question
    chat.answer = answer
    chat.created_at = datetime.now(UTC)
    chat.feedback = feedback

    return chat


@pytest.fixture
def client():

    user = TestUser()
    db = Mock()

    app.dependency_overrides[
        get_current_user
    ] = lambda: user

    def override_db():
        yield db

    app.dependency_overrides[
        get_db
    ] = override_db

    client = TestClient(app)

    yield client

    app.dependency_overrides.clear()


def test_get_chat_history_returns_messages(
    client,
    monkeypatch,
):

    chat = make_chat(
        chat_id=101,
        session_id=10,
        question="What is annual leave?",
        answer="Employees receive annual leave.",
    )

    import app.api.chat_history as module

    monkeypatch.setattr(
        module,
        "get_chat_history",
        lambda **kwargs: [
            (
                chat,
                [
                    (
                        12,
                        "HR_Policy.pdf",
                    )
                ],
            )
        ],
    )

    response = client.get(
        "/chat/sessions/10/messages"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data["messages"]) == 1

    message = data["messages"][0]

    assert message["chat_id"] == 101
    assert message["session_id"] == 10
    assert message["question"] == (
        "What is annual leave?"
    )
    assert message["answer"] == (
        "Employees receive annual leave."
    )

    assert message["sources"] == [
        {
            "document_id": 12,
            "original_filename": "HR_Policy.pdf",
        }
    ]


def test_get_chat_history_returns_404_for_unknown_session(
    client,
    monkeypatch,
):

    import app.api.chat_history as module

    def raise_not_found(**kwargs):
        raise LookupError(
            "Chat session not found."
        )

    monkeypatch.setattr(
        module,
        "get_chat_history",
        raise_not_found,
    )

    response = client.get(
        "/chat/sessions/999/messages"
    )

    assert response.status_code == 404


def test_get_empty_chat_history(
    client,
    monkeypatch,
):

    import app.api.chat_history as module

    monkeypatch.setattr(
        module,
        "get_chat_history",
        lambda **kwargs: [],
    )

    response = client.get(
        "/chat/sessions/10/messages"
    )

    assert response.status_code == 200

    assert response.json() == {
        "messages": []
    }


def test_update_session(
    client,
    monkeypatch,
):

    session = Mock()

    session.session_id = 10
    session.user_id = 1
    session.title = "Updated Session"
    session.created_at = datetime.now(UTC)
    session.last_active = datetime.now(UTC)
    session.is_pinned = True

    import app.api.chat_history as module

    monkeypatch.setattr(
        module,
        "update_chat_session",
        lambda **kwargs: session,
    )

    response = client.patch(
        "/chat/sessions/10",
        json={
            "title": "Updated Session",
            "is_pinned": True,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["session_id"] == 10
    assert data["title"] == "Updated Session"
    assert data["is_pinned"] is True


def test_update_missing_session_returns_404(
    client,
    monkeypatch,
):

    import app.api.chat_history as module


    monkeypatch.setattr(
        module,
        "update_chat_session",
        lambda **kwargs: None,
    )

    response = client.patch(
        "/chat/sessions/999",
        json={
            "title": "Updated",
        },
    )

    assert response.status_code == 404