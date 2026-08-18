from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.chat_history import ChatHistory
from app.models.chat_session import ChatSession
from app.models.chat_source import ChatSource
from app.models.documents import Document
from app.models.users import User
from app.services.rag.rag_service import RAGService

def create_chat_message(*,db:Session,session_id:int,
                        query:str,current_user:User,
                        rag_service:RAGService)->ChatHistory:

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

    #Answer the Query
    rag_result = rag_service.answer(db=db,
                                    query=normalised_query,
                                    current_user=current_user)

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

