from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.dependencies.auth import get_current_user

from app.dto.chat_session import (
    ChatSessionCreateRequest,
    ChatSessionListResponse,
    ChatSessionResponse,
)

from app.models.users import User

from app.services.chat_session_service import (
    create_chat_session,
    get_chat_session,
    get_user_chat_sessions,
    delete_chat_session,
)

router = APIRouter(
    prefix="/chat/sessions",
    tags=["Chat Sessions"]
)

#Create Chat
@router.post(
    "",
    response_model=ChatSessionResponse,
    status_code=status.HTTP_201_CREATED
)
def create_session(
    request: ChatSessionCreateRequest,
    db:Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    return create_chat_session(
        db=db,
        current_user=current_user,
        title=request.title
    )

#Get ALL Chat List
@router.get("",
            response_model=ChatSessionListResponse)

def list_sessions(db: Session=Depends(get_db),
                  current_user: User=Depends(get_current_user)):

    sessions = get_user_chat_sessions(db=db,current_user=current_user)

    return ChatSessionListResponse(sessions=sessions)

@router.get(
    "/{session_id}",
    response_model=ChatSessionResponse,
)
def get_session(session_id: int,
                db: Session = Depends(get_db),
                current_user: User = Depends(get_current_user),
):

    session = get_chat_session(
        db=db,
        session_id=session_id,
        current_user=current_user,
    )

    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found.",
        )

    return session

@router.delete("/{session_id}",status_code=status.HTTP_204_NO_CONTENT)
def delete_session(session_id:int,
                   db:Session=Depends(get_db),
                   current_user: User=Depends(get_current_user)):

    deleted = delete_chat_session(
        db=db,session_id=session_id,current_user=current_user
    )

    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found.",
        )

    return None