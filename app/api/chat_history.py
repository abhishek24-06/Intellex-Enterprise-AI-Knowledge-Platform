from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.dependencies.auth import get_current_user

from app.dto.chat_history import ChatHistoryListResponse,ChatHistoryMessageResponse,ChatHistorySource,ChatSessionUpdateRequest
from app.models.users import User
from app.services.chat_message_service import get_chat_history
from app.services.chat_session_service import update_chat_session,get_chat_session
from app.dto.chat_session import ChatSessionResponse

router = APIRouter(
    prefix="/chat/sessions",
    tags=["Chat History"],
)

@router.get("/{session_id}/messages",response_model=ChatHistoryListResponse)
def get_messages(session_id:int,db:Session=Depends(get_db),current_user:User=Depends(get_current_user)):

    try:
        history = get_chat_history(db=db,session_id=session_id,current_user=current_user)

    except LookupError:
        raise HTTPException(status_code=404,
                            detail="Chat session not found."
        )

    messages: list[ChatHistoryMessageResponse] = []

    for chat, sources in history:

        messages.append(
            ChatHistoryMessageResponse(
                chat_id=chat.chat_id,
                session_id=chat.session_id,
                question=chat.question,
                answer=chat.answer,
                created_at=chat.created_at,
                feedback=(
                    chat.feedback.value
                    if chat.feedback is not None
                    else None
                ),
                sources=[
                    ChatHistorySource(
                        document_id=document_id,
                        original_filename=filename,
                    )
                    for document_id, filename in sources
                ],
            )
        )
    return ChatHistoryListResponse(messages=messages)

@router.patch("/{session_id}",response_model=ChatSessionResponse)
def update_session(
    session_id: int,
    request: ChatSessionUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    session = update_chat_session(
        db=db,
        session_id=session_id,
        current_user=current_user,
        title=request.title,
        is_pinned=request.is_pinned,
    )

    if session is None:
        raise HTTPException(
            status_code=404,
            detail="Chat session not found.",
        )

    return ChatSessionResponse(
        session_id=session.session_id,
        title=session.title,
        created_at=session.created_at,
        last_active=session.last_active,
        is_pinned=session.is_pinned,
    )