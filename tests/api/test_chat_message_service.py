from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import Mock

import pytest

from app.dto.multi_agent_response import MultiAgentResponse
from app.dto.retrieved_chunk import RetrievedChunk
from app.services.chat_message_service import (
    create_chat_message,
)


# ======================================================================
# Helpers
# ======================================================================


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
        metadata={
            "document_id": document_id,
        },
        vector_score=0.8,
        rerank_score=2.5,
    )


def make_agentic_rag_service():
    service = Mock()

    service.answer.return_value = MultiAgentResponse(
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

    return service


def configure_db(
    *,
    session,
    history=None,
):
    db = Mock()

    session_result = Mock()
    session_result.scalar_one_or_none.return_value = session

    history_result = Mock()
    history_result.all.return_value = (
        history or []
    )

    db.execute.side_effect = [
        session_result,
        history_result,
    ]

    return db

def configure_db_with_custom_execute(
    *,
    session,
    history=None,
):
    """
    Utility for tests where the DB may execute more
    than the two initial queries.
    """

    db = Mock()

    session_result = Mock()
    session_result.scalar_one_or_none.return_value = session

    history_result = Mock()
    history_result.all.return_value = (
        history or []
    )

    db.execute.side_effect = [
        session_result,
        history_result,
    ]

    return db


# ======================================================================
# Session ownership
# ======================================================================


def test_session_ownership_is_required():

    db = Mock()

    service = Mock()

    user = make_user()

    result = Mock()

    result.scalar_one_or_none.return_value = None

    db.execute.return_value = result

    contextualizer = Mock()

    with pytest.raises(
        LookupError,
        match="Chat session not found",
    ):
        create_chat_message(
            db=db,
            session_id=10,
            query="Test",
            current_user=user,
            agentic_rag_service=service,
            query_contextualizer=contextualizer,
        )

    service.answer.assert_not_called()


# ======================================================================
# Empty query
# ======================================================================


def test_empty_query_is_rejected():

    session = make_session()

    db = configure_db(
        session=session,
    )

    contextualizer = Mock()

    with pytest.raises(
        ValueError,
        match="Query cannot be empty",
    ):
        create_chat_message(
            db=db,
            session_id=10,
            query="   ",
            current_user=make_user(),
            agentic_rag_service=Mock(),
            query_contextualizer=contextualizer,
        )


# ======================================================================
# Agentic RAG invocation
# ======================================================================


def test_agentic_rag_is_called_with_normalized_query():

    session = make_session()

    db = configure_db(
        session=session,
    )

    contextualizer = Mock()

    agentic_rag_service = (
        make_agentic_rag_service()
    )

    user = make_user()

    db.flush.side_effect = (
        lambda: None
    )

    create_chat_message(
        db=db,
        session_id=10,
        query="   What is deepfake detection?   ",
        current_user=user,
        agentic_rag_service=agentic_rag_service,
        query_contextualizer=contextualizer,
    )

    agentic_rag_service.answer.assert_called_once_with(
        db=db,
        query="What is deepfake detection?",
        current_user=user,
    )


# ======================================================================
# Source deduplication
# ======================================================================


def test_sources_are_deduplicated():

    session = make_session()

    db = configure_db(
        session=session,
    )

    contextualizer = Mock()

    agentic_rag_service = (
        make_agentic_rag_service()
    )

    db.flush.side_effect = (
        lambda: None
    )

    create_chat_message(
        db=db,
        session_id=10,
        query="What is deepfake detection?",
        current_user=make_user(),
        agentic_rag_service=agentic_rag_service,
        query_contextualizer=contextualizer,
    )

    # One ChatHistory
    # +
    # two unique documents
    assert db.add.call_count == 3


# ======================================================================
# Session last_active
# ======================================================================


def test_session_last_active_is_updated():

    session = make_session()

    old_timestamp = session.last_active

    db = configure_db(
        session=session,
    )

    contextualizer = Mock()

    agentic_rag_service = (
        make_agentic_rag_service()
    )

    db.flush.side_effect = (
        lambda: None
    )

    create_chat_message(
        db=db,
        session_id=10,
        query="Test query",
        current_user=make_user(),
        agentic_rag_service=agentic_rag_service,
        query_contextualizer=contextualizer,
    )

    assert (
        session.last_active
        != old_timestamp
    )


# ======================================================================
# Commit
# ======================================================================


def test_database_commit_occurs():

    session = make_session()

    db = configure_db(
        session=session,
    )

    contextualizer = Mock()

    agentic_rag_service = (
        make_agentic_rag_service()
    )

    db.flush.side_effect = (
        lambda: None
    )

    create_chat_message(
        db=db,
        session_id=10,
        query="Test query",
        current_user=make_user(),
        agentic_rag_service=agentic_rag_service,
        query_contextualizer=contextualizer,
    )

    db.commit.assert_called_once()


# ======================================================================
# Commit rollback
# ======================================================================


def test_commit_failure_rolls_back():

    session = make_session()

    db = configure_db(
        session=session,
    )

    db.flush.side_effect = (
        lambda: None
    )

    db.commit.side_effect = RuntimeError(
        "Database failure"
    )

    contextualizer = Mock()

    agentic_rag_service = (
        make_agentic_rag_service()
    )

    with pytest.raises(
        RuntimeError,
        match="Database failure",
    ):
        create_chat_message(
            db=db,
            session_id=10,
            query="Test query",
            current_user=make_user(),
            agentic_rag_service=agentic_rag_service,
            query_contextualizer=contextualizer,
        )

    db.rollback.assert_called_once()


# ======================================================================
# First message
# ======================================================================


def test_first_message_does_not_contextualize():

    session = make_session()

    db = configure_db(
        session=session,
        history=[],
    )

    agentic_rag_service = make_agentic_rag_service()

    contextualizer = Mock()

    current_user = make_user()

    db.flush.side_effect = lambda: None

    create_chat_message(
        db=db,
        session_id=10,
        query="What is annual leave?",
        current_user=current_user,
        agentic_rag_service=agentic_rag_service,
        query_contextualizer=contextualizer,
    )

    contextualizer.contextualize.assert_not_called()

    agentic_rag_service.answer.assert_called_once_with(
        db=db,
        query="What is annual leave?",
        current_user=current_user,
    )

# ======================================================================
# Follow-up contextualization
# ======================================================================


def test_follow_up_message_is_contextualized():

    session = make_session()

    history = [
        (
            "What is the annual leave policy?",
            "Employees receive annual leave.",
        )
    ]

    db = configure_db(
        session=session,
        history=history,
    )

    agentic_rag_service = (
        make_agentic_rag_service()
    )

    contextualizer = Mock()

    contextualizer.contextualize.return_value = (
        "What is the procedure for applying "
        "for annual leave?"
    )

    db.flush.side_effect = (
        lambda: None
    )

    user = make_user()

    create_chat_message(
        db=db,
        session_id=10,
        query="How do I apply for it?",
        current_user=user,
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
        current_user=user,
    )


# ======================================================================
# Database-only response
# ======================================================================


def test_database_only_agentic_response_creates_no_sources():

    session = make_session()

    db = configure_db(
        session=session,
    )

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

    contextualizer = Mock()

    db.flush.side_effect = (
        lambda: None
    )

    chat = create_chat_message(
        db=db,
        session_id=10,
        query="What is my email?",
        current_user=make_user(),
        agentic_rag_service=agentic_rag_service,
        query_contextualizer=contextualizer,
    )

    assert chat.answer == (
        "Your email is "
        "abhishek@example.com."
    )

    # Only ChatHistory is added.
    assert db.add.call_count == 1


# ======================================================================
# Hybrid response
# ======================================================================


def test_hybrid_agentic_response_persists_document_sources():

    session = make_session()

    db = configure_db(
        session=session,
    )

    agentic_rag_service = Mock()

    agentic_rag_service.answer.return_value = (
        MultiAgentResponse(
            query=(
                "What is my department and "
                "what does its policy say?"
            ),
            answer=(
                "You are in Engineering. "
                "Its access policy requires "
                "the approved access process."
            ),
            sources=[
                make_chunk(
                    24,
                    "engineering_policy.pdf",
                ),
                make_chunk(
                    24,
                    "engineering_policy.pdf",
                ),
            ],
        )
    )

    contextualizer = Mock()

    db.flush.side_effect = (
        lambda: None
    )

    create_chat_message(
        db=db,
        session_id=10,
        query=(
            "What is my department and "
            "what does its policy say?"
        ),
        current_user=make_user(),
        agentic_rag_service=agentic_rag_service,
        query_contextualizer=contextualizer,
    )

    # ChatHistory + one unique document.
    assert db.add.call_count == 2


# ======================================================================
# Legacy dependency must not be required
# ======================================================================


def test_agentic_rag_path_does_not_require_legacy_rag_service():

    session = make_session()

    db = configure_db(
        session=session,
    )

    agentic_rag_service = (
        make_agentic_rag_service()
    )

    contextualizer = Mock()

    db.flush.side_effect = (
        lambda: None
    )

    create_chat_message(
        db=db,
        session_id=10,
        query="What is deepfake detection?",
        current_user=make_user(),
        agentic_rag_service=agentic_rag_service,
        query_contextualizer=contextualizer,
    )

    agentic_rag_service.answer.assert_called_once()