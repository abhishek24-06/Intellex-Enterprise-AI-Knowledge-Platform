from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from sqlalchemy.orm import Session

from app.database.database import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.agentic_rag import (
    get_agentic_rag_service,
)

from app.dependencies.rag import get_query_contextualizer
from app.dto.chat import (
    ChatQueryRequest,
    ChatQueryResponse,
    ChatSource,
)

from app.models.users import User

from app.services.agentic_rag_service import (
    AgenticRAGService,
)

from app.services.chat_message_service import (
    create_chat_message,
    get_chat_sources,
)

from app.services.query_contextualizer import (
    QueryContextualizer,
)


router = APIRouter(
    prefix="/chat/sessions",
    tags=["Chat Messages"],
)


@router.post(
    "/{session_id}/messages",
    response_model=ChatQueryResponse,
    status_code=status.HTTP_201_CREATED,
)
def send_messages(
    session_id: int,
    request: ChatQueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        get_current_user
    ),
    agentic_rag_service: AgenticRAGService = Depends(
        get_agentic_rag_service
    ),
    query_contextualizer: QueryContextualizer = Depends(
        get_query_contextualizer
    ),
):

    try:

        chat_history = create_chat_message(
            db=db,
            session_id=session_id,
            query=request.query,
            current_user=current_user,
            agentic_rag_service=agentic_rag_service,
            query_contextualizer=query_contextualizer,
        )

    except LookupError:

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat session not found.",
        )

    sources = get_chat_sources(
        db=db,
        chat_id=chat_history.chat_id,
    )

    return ChatQueryResponse(
        query=chat_history.question,
        answer=chat_history.answer,
        sources=[
            ChatSource(
                document_id=document_id,
                original_filename=filename,
            )
            for document_id, filename in sources
        ],
    )