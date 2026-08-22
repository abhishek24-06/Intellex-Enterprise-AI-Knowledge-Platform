from __future__ import annotations

from unittest.mock import Mock

import pytest
from sqlalchemy import select

from app.database.database import SessionLocal
from app.dto.multi_agent_response import (
    MultiAgentResponse,
)
from app.dto.retrieved_chunk import (
    RetrievedChunk,
)
from app.models.chat_history import (
    ChatHistory,
)
from app.models.chat_session import (
    ChatSession,
)
from app.models.chat_source import (
    ChatSource,
)
from app.models.documents import (
    Document,
)
from app.models.users import (
    User,
)
from app.services.chat_message_service import (
    create_chat_message,
    get_chat_sources,
)


# ======================================================================
# DATABASE
# ======================================================================


@pytest.fixture
def db():
    """
    Real PostgreSQL/Supabase session.

    Test-created data is rolled back and the session
    is closed after each test.
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
    Use an existing active user that belongs to an organization.
    """

    user = db.execute(
        select(User)
        .where(
            User.is_active.is_(True),
            User.organization_id.is_not(None),
        )
        .order_by(
            User.user_id.asc()
        )
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
def chat_session(
    db,
    test_user,
):
    """
    Create a real temporary ChatSession.
    """

    session = ChatSession(
        user_id=test_user.user_id,
        title="Agentic RAG Integration Test",
        is_pinned=False,
    )

    db.add(session)
    db.commit()
    db.refresh(session)

    return session


# ======================================================================
# AGENTIC RAG FIXTURES
# ======================================================================


def make_retrieved_chunk(
    *,
    document_id: int,
    filename: str,
    text: str,
):
    return RetrievedChunk(
        document_id=document_id,
        original_filename=filename,
        chunk_id=100,
        chunk_index=0,
        chunk_text=text,
        token_count=30,
        metadata={
            "document_id": document_id,
        },
        vector_score=0.90,
        rerank_score=0.90,
    )


@pytest.fixture
def agentic_rag_service():

    service = Mock()

    service.answer.return_value = (
        MultiAgentResponse(
            query=(
                "Tell me about the deepfake "
                "detection system"
            ),
            answer=(
                "The deepfake detection system "
                "uses deep learning and computer "
                "vision techniques."
            ),
            sources=[
                make_retrieved_chunk(
                    document_id=24,
                    filename="report.docx",
                    text=(
                        "Deepfake detection "
                        "system content."
                    ),
                ),
                make_retrieved_chunk(
                    document_id=24,
                    filename="report.docx",
                    text=(
                        "Deepfake detector "
                        "conclusion."
                    ),
                ),
                make_retrieved_chunk(
                    document_id=28,
                    filename="research.docx",
                    text=(
                        "Deepfake detection "
                        "background."
                    ),
                ),
            ],
        )
    )

    return service


# ======================================================================
# HELPERS
# ======================================================================


def assert_chat_history_exists(
    *,
    db,
    chat_id: int,
    session_id: int,
    expected_question: str,
):
    chat = db.execute(
        select(ChatHistory)
        .where(
            ChatHistory.chat_id
            == chat_id,
        )
    ).scalar_one_or_none()

    assert chat is not None

    assert (
        chat.session_id
        == session_id
    )

    assert (
        chat.question
        == expected_question
    )

    assert chat.answer

    return chat


def get_source_rows(
    *,
    db,
    chat_id: int,
):
    return db.execute(
        select(ChatSource)
        .where(
            ChatSource.chat_id
            == chat_id,
        )
        .order_by(
            ChatSource.source_id.asc()
        )
    ).scalars().all()


# ======================================================================
# 1. REAL CHAT MESSAGE PERSISTENCE
# ======================================================================


def test_real_agentic_chat_message_persistence(
    db,
    test_user,
    chat_session,
    agentic_rag_service,
):
    """
    Real persistence flow:

        Existing User
             ↓
        ChatSession
             ↓
        AgenticRAGService
             ↓
        ChatHistory
             ↓
        ChatSource[]
             ↓
        last_active
    """

    query = (
        "Tell me about the deepfake "
        "detection system"
    )

    old_last_active = (
        chat_session.last_active
    )

    chat = create_chat_message(
        db=db,
        session_id=chat_session.session_id,
        query=query,
        current_user=test_user,
        agentic_rag_service=agentic_rag_service,
    )

    # --------------------------------------------------------------
    # ChatHistory
    # --------------------------------------------------------------

    assert chat.chat_id is not None

    assert (
        chat.session_id
        == chat_session.session_id
    )

    assert chat.question == query

    assert chat.answer

    # --------------------------------------------------------------
    # Agentic RAG call
    # --------------------------------------------------------------

    agentic_rag_service.answer.assert_called_once_with(
        db=db,
        query=query,
        current_user=test_user,
    )

    # --------------------------------------------------------------
    # Persisted row
    # --------------------------------------------------------------

    persisted_chat = (
        assert_chat_history_exists(
            db=db,
            chat_id=chat.chat_id,
            session_id=chat_session.session_id,
            expected_question=query,
        )
    )

    assert (
        persisted_chat.answer
        == chat.answer
    )

    # --------------------------------------------------------------
    # Sources
    # --------------------------------------------------------------

    source_rows = get_source_rows(
        db=db,
        chat_id=chat.chat_id,
    )

    assert source_rows

    # --------------------------------------------------------------
    # Source documents must exist
    # --------------------------------------------------------------

    for source in source_rows:

        document = db.execute(
            select(Document)
            .where(
                Document.document_id
                == source.document_id,
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

    # The mock graph provided documents 24 and 28.
    assert set(document_ids) == {
        24,
        28,
    }

    # --------------------------------------------------------------
    # Session last_active
    # --------------------------------------------------------------

    refreshed_session = db.execute(
        select(ChatSession)
        .where(
            ChatSession.session_id
            == chat_session.session_id,
        )
    ).scalar_one()

    assert (
        refreshed_session.last_active
        >= old_last_active
    )


# ======================================================================
# 2. GET CHAT SOURCES
# ======================================================================


def test_get_chat_sources_returns_document_metadata(
    db,
    test_user,
    chat_session,
    agentic_rag_service,
):
    query = (
        "Tell me about the deepfake "
        "detection system"
    )

    chat = create_chat_message(
        db=db,
        session_id=chat_session.session_id,
        query=query,
        current_user=test_user,
        agentic_rag_service=agentic_rag_service,
    )

    sources = get_chat_sources(
        db=db,
        chat_id=chat.chat_id,
    )

    assert sources

    for (
        document_id,
        original_filename,
    ) in sources:

        assert isinstance(
            document_id,
            int,
        )

        assert original_filename

        assert isinstance(
            original_filename,
            str,
        )

    assert {
        document_id
        for document_id, _
        in sources
    } == {
        24,
        28,
    }


# ======================================================================
# 3. DATABASE-ONLY CHAT
# ======================================================================


def test_database_only_message_creates_no_chat_sources(
    db,
    test_user,
    chat_session,
):
    agentic_rag_service = Mock()

    agentic_rag_service.answer.return_value = (
        MultiAgentResponse(
            query="What is my email?",
            answer=(
                "Your email is "
                "abhishek@example.com."
            ),
            sources=[],
        )
    )

    chat = create_chat_message(
        db=db,
        session_id=chat_session.session_id,
        query="What is my email?",
        current_user=test_user,
        agentic_rag_service=agentic_rag_service,
    )

    assert chat.answer == (
        "Your email is "
        "abhishek@example.com."
    )

    source_rows = get_source_rows(
        db=db,
        chat_id=chat.chat_id,
    )

    assert source_rows == []


# ======================================================================
# 4. HYBRID MESSAGE
# ======================================================================


def test_hybrid_message_persists_knowledge_sources(
    db,
    test_user,
    chat_session,
):
    agentic_rag_service = Mock()

    agentic_rag_service.answer.return_value = (
        MultiAgentResponse(
            query=(
                "What is my department and "
                "what does its access policy say?"
            ),
            answer=(
                "You are in Engineering. "
                "The Engineering access policy "
                "requires the approved access process."
            ),
            sources=[
                make_retrieved_chunk(
                    document_id=24,
                    filename="engineering_policy.pdf",
                    text=(
                        "Engineering employees "
                        "must use the approved "
                        "access request process."
                    ),
                ),
            ],
        )
    )

    chat = create_chat_message(
        db=db,
        session_id=chat_session.session_id,
        query=(
            "What is my department and "
            "what does its access policy say?"
        ),
        current_user=test_user,
        agentic_rag_service=agentic_rag_service,
    )

    assert chat.answer

    source_rows = get_source_rows(
        db=db,
        chat_id=chat.chat_id,
    )

    assert len(source_rows) == 1

    assert source_rows[0].document_id == 24


# ======================================================================
# 5. SESSION OWNERSHIP
# ======================================================================


def test_user_cannot_post_to_another_users_session(
    db,
    test_user,
    agentic_rag_service,
):
    """
    A user must not be able to write to another
    user's session even if they know the session ID.
    """

    other_user = db.execute(
        select(User)
        .where(
            User.user_id
            != test_user.user_id,
            User.is_active.is_(True),
            User.organization_id.is_not(None),
        )
        .order_by(
            User.user_id.asc()
        )
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
            agentic_rag_service=agentic_rag_service,
        )

    agentic_rag_service.answer.assert_not_called()


# ======================================================================
# 6. QUERY NORMALIZATION
# ======================================================================


def test_query_is_trimmed_before_persistence(
    db,
    test_user,
    chat_session,
    agentic_rag_service,
):
    query = (
        "   Tell me about the deepfake "
        "detection system   "
    )

    chat = create_chat_message(
        db=db,
        session_id=chat_session.session_id,
        query=query,
        current_user=test_user,
        agentic_rag_service=agentic_rag_service,
    )

    assert chat.question == (
        "Tell me about the deepfake "
        "detection system"
    )

    agentic_rag_service.answer.assert_called_once_with(
        db=db,
        query=(
            "Tell me about the deepfake "
            "detection system"
        ),
        current_user=test_user,
    )


# ======================================================================
# 7. EMPTY QUERY
# ======================================================================


def test_empty_query_is_rejected(
    db,
    test_user,
    chat_session,
    agentic_rag_service,
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
            agentic_rag_service=agentic_rag_service,
        )

    agentic_rag_service.answer.assert_not_called()


# ======================================================================
# 8. FOLLOW-UP CONTEXTUALIZATION
# ======================================================================


def test_follow_up_is_contextualized_before_agentic_rag(
    db,
    test_user,
    chat_session,
    agentic_rag_service,
):
    """
    This verifies that the existing conversation
    contextualization layer still sits before AgenticRAGService.
    """

    # Create a previous message directly.
    previous_chat = ChatHistory(
        session_id=chat_session.session_id,
        question=(
            "What is the annual leave policy?"
        ),
        answer=(
            "Employees receive annual leave."
        ),
    )

    db.add(previous_chat)
    db.commit()

    contextualizer = Mock()

    contextualizer.contextualize.return_value = (
        "What is the procedure for applying "
        "for annual leave?"
    )

    create_chat_message(
        db=db,
        session_id=chat_session.session_id,
        query="How do I apply for it?",
        current_user=test_user,
        agentic_rag_service=agentic_rag_service,
        query_contextualizer=contextualizer,
    )

    contextualizer.contextualize.assert_called_once_with(
        query="How do I apply for it?",
        history=[
            (
                "What is the annual leave policy?",
                "Employees receive annual leave.",
            )
        ],
    )

    agentic_rag_service.answer.assert_called_once_with(
        db=db,
        query=(
            "What is the procedure for applying "
            "for annual leave?"
        ),
        current_user=test_user,
    )