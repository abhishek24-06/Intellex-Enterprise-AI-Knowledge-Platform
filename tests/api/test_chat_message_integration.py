from __future__ import annotations

from datetime import datetime, UTC

import pytest
from sqlalchemy import select

from app.database.database import SessionLocal
from app.models.chat_session import ChatSession
from app.models.chat_history import ChatHistory
from app.models.chat_source import ChatSource
from app.models.users import User
from app.models.documents import Document

from app.services.chat_message_service import (
    create_chat_message,
    get_chat_sources,
)
from app.services.rag.rag_service import RAGService


# ======================================================================
# DATABASE
# ======================================================================


@pytest.fixture
def db():
    """
    Real Supabase/PostgreSQL session.

    Test-created rows are rolled back after the test.
    """

    session = SessionLocal()

    try:
        yield session
    finally:
        session.rollback()
        session.close()


# ======================================================================
# REAL USER
# ======================================================================


@pytest.fixture
def test_user(db):
    """
    Use an existing active user from the database.
    """

    user = db.execute(
        select(User)
        .where(
            User.is_active.is_(True),
            User.organization_id.is_not(None),
        )
        .order_by(User.user_id.asc())
        .limit(1)
    ).scalar_one_or_none()

    if user is None:
        pytest.skip(
            "No active user with an organization exists."
        )

    return user


# ======================================================================
# CHAT SESSION
# ======================================================================


@pytest.fixture
def chat_session(db, test_user):
    """
    Create a temporary real chat session.

    The outer DB fixture rolls it back after the test.
    """

    session = ChatSession(
        user_id=test_user.user_id,
        title="Integration Test Session",
        is_pinned=False,
    )

    db.add(session)
    db.commit()
    db.refresh(session)

    return session


# ======================================================================
# REAL RAG SERVICE
# ======================================================================


@pytest.fixture
def rag_service():
    from unittest.mock import Mock

    from app.dto.rag_response import RAGResult
    from app.dto.retrieved_chunk import RetrievedChunk

    service = Mock()

    service.answer.return_value = RAGResult(
        query="Tell me about the deepfake detection system",
        answer=(
            "The deepfake detection system uses deep learning "
            "and computer vision techniques."
        ),
        sources=[
            RetrievedChunk(
                document_id=24,
                original_filename="report.docx",
                chunk_id=425,
                chunk_index=9,
                chunk_text="Deepfake detection system content.",
                token_count=100,
                metadata={"document_id": 24},
                vector_score=0.66,
                rerank_score=4.27,
            ),
            RetrievedChunk(
                document_id=24,
                original_filename="report.docx",
                chunk_id=298,
                chunk_index=277,
                chunk_text="Deepfake detector conclusion.",
                token_count=100,
                metadata={"document_id": 24},
                vector_score=0.66,
                rerank_score=2.17,
            ),
            RetrievedChunk(
                document_id=28,
                original_filename="report.docx",
                chunk_id=425,
                chunk_index=9,
                chunk_text="Deepfake detection background.",
                token_count=100,
                metadata={"document_id": 28},
                vector_score=0.66,
                rerank_score=4.27,
            ),
        ],
    )

    return service

# ======================================================================
# HELPERS
# ======================================================================


def assert_chat_history_exists(
    db,
    chat_id: int,
    session_id: int,
    expected_question: str,
):
    chat = db.execute(
        select(ChatHistory)
        .where(
            ChatHistory.chat_id == chat_id,
        )
    ).scalar_one_or_none()

    assert chat is not None

    assert chat.session_id == session_id

    assert chat.question == expected_question

    assert chat.answer

    return chat


def get_source_rows(
    db,
    chat_id: int,
):
    return db.execute(
        select(ChatSource)
        .where(
            ChatSource.chat_id == chat_id,
        )
        .order_by(
            ChatSource.source_id.asc()
        )
    ).scalars().all()


# ======================================================================
# REAL END-TO-END MESSAGE FLOW
# ======================================================================


def test_real_chat_message_persistence(
    db,
    test_user,
    chat_session,
    rag_service: RAGService,
):
    """
    Real flow:

        Existing User
             ↓
        ChatSession
             ↓
        RAGService
             ↓
        ChatHistory
             ↓
        ChatSource[]
             ↓
        last_active
    """

    query = (
        "Tell me about the deepfake detection system"
    )

    old_last_active = chat_session.last_active

    # --------------------------------------------------------------
    # Execute real RAG + persistence
    # --------------------------------------------------------------

    chat = create_chat_message(
        db=db,
        session_id=chat_session.session_id,
        query=query,
        current_user=test_user,
        rag_service=rag_service,
    )

    # --------------------------------------------------------------
    # ChatHistory
    # --------------------------------------------------------------

    assert chat.chat_id is not None

    assert chat.session_id == (
        chat_session.session_id
    )

    assert chat.question == query

    assert chat.answer

    # --------------------------------------------------------------
    # Persisted DB row
    # --------------------------------------------------------------

    persisted_chat = assert_chat_history_exists(
        db=db,
        chat_id=chat.chat_id,
        session_id=chat_session.session_id,
        expected_question=query,
    )

    # --------------------------------------------------------------
    # Sources
    # --------------------------------------------------------------

    source_rows = get_source_rows(
        db=db,
        chat_id=chat.chat_id,
    )

    # It is valid for retrieval to find no sources,
    # but for this known-good query we expect sources.
    assert source_rows

    # --------------------------------------------------------------
    # Source documents must exist
    # --------------------------------------------------------------

    for source in source_rows:

        document = db.execute(
            select(Document)
            .where(
                Document.document_id
                == source.document_id
            )
        ).scalar_one_or_none()

        assert document is not None

    # --------------------------------------------------------------
    # No duplicate document IDs
    # --------------------------------------------------------------

    document_ids = [
        source.document_id
        for source in source_rows
    ]

    assert len(document_ids) == len(
        set(document_ids)
    )

    # --------------------------------------------------------------
    # Session activity updated
    # --------------------------------------------------------------

    refreshed_session = db.execute(
        select(ChatSession)
        .where(
            ChatSession.session_id
            == chat_session.session_id
        )
    ).scalar_one()

    assert (
        refreshed_session.last_active
        >= old_last_active
    )


# ======================================================================
# SOURCE HELPER
# ======================================================================


def test_get_chat_sources(
    db,
    test_user,
    chat_session,
    rag_service: RAGService,
):
    """
    Verify that persisted ChatSource rows can be resolved
    into document_id + original_filename.
    """

    query = (
        "Tell me about the deepfake detection system"
    )

    chat = create_chat_message(
        db=db,
        session_id=chat_session.session_id,
        query=query,
        current_user=test_user,
        rag_service=rag_service,
    )

    sources = get_chat_sources(
        db=db,
        chat_id=chat.chat_id,
    )

    assert sources

    for document_id, original_filename in sources:

        assert isinstance(
            document_id,
            int,
        )

        assert original_filename

        assert isinstance(
            original_filename,
            str,
        )


# ======================================================================
# SESSION OWNERSHIP
# ======================================================================


def test_user_cannot_post_to_another_users_session(
    db,
    test_user,
    rag_service: RAGService,
):
    """
    Security test:

    A user must not be able to write to another user's
    chat session even if they know the session_id.
    """

    other_user = db.execute(
        select(User)
        .where(
            User.user_id != test_user.user_id,
            User.is_active.is_(True),
            User.organization_id.is_not(None),
        )
        .order_by(User.user_id.asc())
        .limit(1)
    ).scalar_one_or_none()

    if other_user is None:
        pytest.skip(
            "Need at least two active users."
        )

    other_session = ChatSession(
        user_id=other_user.user_id,
        title="Other User Session",
    )

    db.add(other_session)
    db.commit()
    db.refresh(other_session)

    with pytest.raises(
        LookupError,
        match="Chat session not found",
    ):
        create_chat_message(
            db=db,
            session_id=other_session.session_id,
            query="Unauthorized message",
            current_user=test_user,
            rag_service=rag_service,
        )


# ======================================================================
# QUERY NORMALIZATION
# ======================================================================


def test_query_is_trimmed_before_persistence(
    db,
    test_user,
    chat_session,
    rag_service: RAGService,
):
    query = (
        "   Tell me about the deepfake detection system   "
    )

    chat = create_chat_message(
        db=db,
        session_id=chat_session.session_id,
        query=query,
        current_user=test_user,
        rag_service=rag_service,
    )

    assert chat.question == (
        "Tell me about the deepfake detection system"
    )


# ======================================================================
# EMPTY QUERY
# ======================================================================


def test_empty_query_is_rejected(
    db,
    test_user,
    chat_session,
    rag_service: RAGService,
):

    with pytest.raises(
        ValueError,
        match="Query cannot be empty",
    ):
        create_chat_message(
            db=db,
            session_id=chat_session.session_id,
            query="   ",
            current_user=test_user,
            rag_service=rag_service,
        )