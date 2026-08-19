from __future__ import annotations
from time import perf_counter
from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.chat_history import ChatHistory
from app.models.chat_session import ChatSession
from app.models.chat_source import ChatSource
from app.models.documents import Document
from app.models.users import User
from app.services.observability.rag_trace import RAGTrace
from app.services.rag.rag_service import RAGService
from app.services.query_contextualizer import QueryContextualizer

MAX_CONTEXT_MESSAGES = 10

def get_recent_chat_history(*,db:Session,session_id:int,limit:int = MAX_CONTEXT_MESSAGES)->list[tuple[str,str]]:

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

def create_chat_message(*,db:Session,session_id:int,
                        query:str,current_user:User,
                        rag_service:RAGService,
                        query_contextualizer: QueryContextualizer)->ChatHistory:

    session = db.execute(
        select(ChatSession)
        .where(
            ChatSession.session_id == session_id,
            ChatSession.user_id == current_user.user_id,
        )
    ).scalar_one_or_none()

    if session is None:
        raise LookupError("Chat session not found.")

    session.last_active = datetime.now(UTC)

    normalised_query = query.strip()

    if not normalised_query:
        raise ValueError("Query cannot be empty.")

    history = get_recent_chat_history(
        db=db,
        session_id=session.session_id,
    )

    contextualization_started = perf_counter()

    retrieval_query = (
        query_contextualizer.contextualize(
            query=normalised_query,
            history=history,
        )
        if history
        else normalised_query
    )

    contextualization_latency_ms = (perf_counter() - contextualization_started) * 1000

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

    #Answer the Query
    rag_result = rag_service.answer(db=db,
                                    query=retrieval_query,
                                    current_user=current_user,
                                    trace=trace)

    chat_history = ChatHistory(
        session_id = session.session_id,
        question=normalised_query,
        answer=rag_result.answer
    )

    db.add(chat_history)
    db.flush()

    seen_document_ids: set[int] = set() #Remembers already processed Doc to keep only unique save

    for chunk in rag_result.sources: #Loop thru retrieved chunk
        if chunk.document_id in seen_document_ids:
            continue

        seen_document_ids.add(chunk.document_id)

        db.add(
            ChatSource(  #Stores Doc used to answer
                chat_id=chat_history.chat_id,
                document_id=chunk.document_id,
            )
        )

    session.last_active = datetime.now(UTC)

    try:
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(chat_history)

    return chat_history

def get_chat_sources(*,db:Session,chat_id: int)->list[tuple[int,str]]:

    #Returns document used to answer

    rows = db.execute(
        select(
            ChatSource.document_id,
            Document.original_filename,
        )
        .join(
            Document,
            Document.document_id == ChatSource.document_id,
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

def get_chat_history(*,db: Session,session_id: int,current_user: User,) -> list[
    tuple[
        ChatHistory,
        list[tuple[int, str]],
    ]
]:

    session_exists = db.execute(
        select(ChatSession.session_id)
        .where(
            ChatSession.session_id == session_id,
            ChatSession.user_id == current_user.user_id,
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
            ChatSource.chat_id == ChatHistory.chat_id,
        )
        .outerjoin(
            Document,
            Document.document_id == ChatSource.document_id,
        )
        .where(
            ChatHistory.session_id == session_id,
        )
        .order_by(
            ChatHistory.created_at.asc(),
            ChatHistory.chat_id.asc(),
            ChatSource.source_id.asc(),
        )
    ).all()

    grouped: dict[
        int,
        tuple[ChatHistory, list[tuple[int, str]]]
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

    return list(grouped.values())