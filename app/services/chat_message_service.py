from __future__ import annotations

from datetime import UTC, datetime
from time import perf_counter
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.chat_history import ChatHistory
from app.models.chat_session import ChatSession
from app.models.chat_source import ChatSource
from app.models.documents import Document
from app.models.users import User

from app.services.agentic_rag_service import AgenticRAGService
from app.services.observability.rag_trace import RAGTrace
from app.services.query_contextualizer import QueryContextualizer
from app.services.rag.rag_service import RAGService


MAX_CONTEXT_MESSAGES = 10


def get_recent_chat_history(
    *,
    db: Session,
    session_id: int,
    limit: int = MAX_CONTEXT_MESSAGES,
) -> list[tuple[str, str]]:

    rows = db.execute(
        select(
            ChatHistory.question,
            ChatHistory.answer,
        )
        .where(
            ChatHistory.session_id == session_id,
        )
        .order_by(
            ChatHistory.created_at.desc(),
            ChatHistory.chat_id.desc(),
        )
        .limit(limit)
    ).all()

    return [
        (question, answer)
        for question, answer in reversed(rows)
    ]


def create_chat_message(
    *,
    db: Session,
    session_id: int,
    query: str,
    current_user: User,
    query_contextualizer: QueryContextualizer,
    agentic_rag_service: AgenticRAGService | None = None,
    rag_service: RAGService | None = None,
) -> ChatHistory:

    # --------------------------------------------------------------
    # 1. Verify session belongs to current user
    # --------------------------------------------------------------

    session = db.execute(
        select(ChatSession)
        .where(
            ChatSession.session_id == session_id,
            ChatSession.user_id == current_user.user_id,
        )
    ).scalar_one_or_none()

    if session is None:
        raise LookupError(
            "Chat session not found."
        )

    # --------------------------------------------------------------
    # 2. Normalize query
    # --------------------------------------------------------------

    normalised_query = query.strip()

    if not normalised_query:
        raise ValueError(
            "Query cannot be empty."
        )

    # --------------------------------------------------------------
    # 3. Retrieve recent conversation history
    # --------------------------------------------------------------

    history = get_recent_chat_history(
        db=db,
        session_id=session.session_id,
    )

    # --------------------------------------------------------------
    # 4. Contextualize follow-up query
    # --------------------------------------------------------------

    contextualization_started = perf_counter()

    retrieval_query = (
        query_contextualizer.contextualize(
            query=normalised_query,
            history=history,
        )
        if history
        else normalised_query
    )

    contextualization_latency_ms = (
        perf_counter()
        - contextualization_started
    ) * 1000

    # --------------------------------------------------------------
    # 5. Observability trace
    # --------------------------------------------------------------

    trace = RAGTrace(
        request_id=str(uuid4()),
        user_id=current_user.user_id,
        organization_id=current_user.organization_id,
        session_id=session.session_id,
        original_query=normalised_query,
        retrieval_query=retrieval_query,
        contextualization_latency_ms=(
            contextualization_latency_ms
        ),
    )

    # --------------------------------------------------------------
    # 6. Agentic RAG
    #
    # New production path:
    #
    # Agent 4
    #   ↓
    # Agent 1 / Agent 3 / Hybrid
    #   ↓
    # Synthesis
    #   ↓
    # Agent 2
    #   ↓
    # Final answer
    # --------------------------------------------------------------

    if agentic_rag_service is not None:

        agentic_result = agentic_rag_service.answer(
            db=db,
            query=retrieval_query,
            current_user=current_user,
        )

        answer = agentic_result.answer
        sources = agentic_result.sources

    # --------------------------------------------------------------
    # 7. Legacy fallback
    #
    # This allows the existing service tests and callers to continue
    # working during the migration.
    # --------------------------------------------------------------

    elif rag_service is not None:

        rag_result = rag_service.answer(
            db=db,
            query=retrieval_query,
            current_user=current_user,
            trace=trace,
        )

        answer = rag_result.answer
        sources = rag_result.sources

    else:

        raise RuntimeError(
            "Either agentic_rag_service or rag_service "
            "must be provided."
        )

    # --------------------------------------------------------------
    # 8. Persist ChatHistory
    # --------------------------------------------------------------

    chat_history = ChatHistory(
        session_id=session.session_id,
        question=normalised_query,
        answer=answer,
    )

    db.add(chat_history)
    db.flush()

    # --------------------------------------------------------------
    # 9. Persist document sources
    #
    # Database-only requests produce sources=[].
    #
    # Knowledge and Hybrid requests contain RAG sources.
    # --------------------------------------------------------------

    seen_document_ids: set[int] = set()

    for chunk in sources:

        if chunk.document_id in seen_document_ids:
            continue

        seen_document_ids.add(
            chunk.document_id
        )

        db.add(
            ChatSource(
                chat_id=chat_history.chat_id,
                document_id=chunk.document_id,
            )
        )

    # --------------------------------------------------------------
    # 10. Update session activity
    # --------------------------------------------------------------

    session.last_active = datetime.now(UTC)

    # --------------------------------------------------------------
    # 11. Commit transaction
    # --------------------------------------------------------------

    try:
        db.commit()

    except Exception:
        db.rollback()
        raise

    db.refresh(chat_history)

    return chat_history


def get_chat_sources(
    *,
    db: Session,
    chat_id: int,
) -> list[tuple[int, str]]:

    rows = db.execute(
        select(
            ChatSource.document_id,
            Document.original_filename,
        )
        .join(
            Document,
            Document.document_id
            == ChatSource.document_id,
        )
        .where(
            ChatSource.chat_id == chat_id,
        )
        .order_by(
            ChatSource.source_id.asc()
        )
    ).all()

    return [
        (
            document_id,
            original_filename,
        )
        for document_id, original_filename in rows
    ]


def get_chat_history(
    *,
    db: Session,
    session_id: int,
    current_user: User,
) -> list[
    tuple[
        ChatHistory,
        list[tuple[int, str]],
    ]
]:

    session_exists = db.execute(
        select(ChatSession.session_id)
        .where(
            ChatSession.session_id == session_id,
            ChatSession.user_id
            == current_user.user_id,
        )
    ).scalar_one_or_none()

    if session_exists is None:
        raise LookupError(
            "Chat session not found."
        )

    rows = db.execute(
        select(
            ChatHistory,
            ChatSource.document_id,
            Document.original_filename,
        )
        .outerjoin(
            ChatSource,
            ChatSource.chat_id
            == ChatHistory.chat_id,
        )
        .outerjoin(
            Document,
            Document.document_id
            == ChatSource.document_id,
        )
        .where(
            ChatHistory.session_id
            == session_id,
        )
        .order_by(
            ChatHistory.created_at.asc(),
            ChatHistory.chat_id.asc(),
            ChatSource.source_id.asc(),
        )
    ).all()

    grouped: dict[
        int,
        tuple[
            ChatHistory,
            list[tuple[int, str]],
        ],
    ] = {}

    for (
        chat_history,
        document_id,
        original_filename,
    ) in rows:

        if chat_history.chat_id not in grouped:
            grouped[chat_history.chat_id] = (
                chat_history,
                [],
            )

        if (
            document_id is not None
            and original_filename is not None
        ):
            grouped[
                chat_history.chat_id
            ][1].append(
                (
                    document_id,
                    original_filename,
                )
            )

    return list(
        grouped.values()
    )