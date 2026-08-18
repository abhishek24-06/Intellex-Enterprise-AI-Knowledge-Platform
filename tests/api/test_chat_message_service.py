from datetime import datetime, UTC
from unittest.mock import Mock

import pytest

from app.dto.rag_response import RAGResult
from app.dto.retrieved_chunk import RetrievedChunk
from app.models.chat_history import ChatHistory
from app.services.chat_message_service import (
    create_chat_message,
)


def make_user():
    user = Mock()
    user.user_id = 1
    user.organization_id = 2
    return user


def make_session():
    session = Mock()
    session.session_id = 10
    session.user_id = 1
    session.last_active = datetime.now(UTC)
    return session


def make_chunk(
    document_id: int,
    filename: str,
):
    return RetrievedChunk(
        document_id=document_id,
        original_filename=filename,
        chunk_id=100,
        chunk_index=0,
        chunk_text="Test context",
        token_count=10,
        metadata={},
        vector_score=0.8,
        rerank_score=2.5,
    )


def make_rag_service():

    rag_service = Mock()

    rag_service.answer.return_value = RAGResult(
        query="What is deepfake detection?",
        answer="It uses CNNs.",
        sources=[
            make_chunk(
                24,
                "deepfake.pdf",
            ),
            make_chunk(
                24,
                "deepfake.pdf",
            ),
            make_chunk(
                28,
                "research.docx",
            ),
        ],
    )

    return rag_service


def configure_db(
    *,
    session,
):
    db = Mock()

    execute_result = Mock()
    execute_result.scalar_one_or_none.return_value = session

    db.execute.return_value = execute_result

    return db


def test_session_ownership_is_required():

    db = Mock()
    rag_service = Mock()
    user = make_user()

    result = Mock()
    result.scalar_one_or_none.return_value = None

    db.execute.return_value = result

    with pytest.raises(
        LookupError,
        match="Chat session not found",
    ):
        create_chat_message(
            db=db,
            session_id=10,
            query="Test",
            current_user=user,
            rag_service=rag_service,
        )

    rag_service.answer.assert_not_called()


def test_empty_query_is_rejected():

    session = make_session()

    db = configure_db(
        session=session,
    )

    with pytest.raises(
        ValueError,
        match="Query cannot be empty",
    ):
        create_chat_message(
            db=db,
            session_id=10,
            query="   ",
            current_user=make_user(),
            rag_service=Mock(),
        )

def test_rag_is_called_with_normalized_query():

    session = make_session()

    db = configure_db(
        session=session,
    )

    rag_service = make_rag_service()

    user = make_user()

    db.flush.side_effect = lambda: None

    create_chat_message(
        db=db,
        session_id=10,
        query="   What is deepfake detection?   ",
        current_user=user,
        rag_service=rag_service,
    )

    rag_service.answer.assert_called_once_with(
        db=db,
        query="What is deepfake detection?",
        current_user=user,
    )

def test_sources_are_deduplicated():

    session = make_session()
    db = configure_db(
        session=session,
    )

    rag_service = make_rag_service()

    db.flush.side_effect = lambda: None

    create_chat_message(
        db=db,
        session_id=10,
        query="What is deepfake detection?",
        current_user=make_user(),
        rag_service=rag_service,
    )

    # ChatHistory + 2 unique ChatSource objects
    assert db.add.call_count == 3


def test_session_last_active_is_updated():

    session = make_session()

    old_timestamp = session.last_active

    db = configure_db(
        session=session,
    )

    rag_service = make_rag_service()

    db.flush.side_effect = lambda: None

    create_chat_message(
        db=db,
        session_id=10,
        query="Test query",
        current_user=make_user(),
        rag_service=rag_service,
    )

    assert session.last_active != old_timestamp

def test_database_commit_occurs():

    session = make_session()

    db = configure_db(
        session=session,
    )

    rag_service = make_rag_service()

    db.flush.side_effect = lambda: None

    create_chat_message(
        db=db,
        session_id=10,
        query="Test query",
        current_user=make_user(),
        rag_service=rag_service,
    )

    db.commit.assert_called_once()


def test_commit_failure_rolls_back():

    session = make_session()

    db = configure_db(
        session=session,
    )

    db.flush.side_effect = lambda: None

    db.commit.side_effect = RuntimeError(
        "Database failure"
    )

    rag_service = make_rag_service()

    with pytest.raises(
        RuntimeError,
        match="Database failure",
    ):
        create_chat_message(
            db=db,
            session_id=10,
            query="Test query",
            current_user=make_user(),
            rag_service=rag_service,
        )

    db.rollback.assert_called_once()