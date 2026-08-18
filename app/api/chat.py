from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.dependencies.auth import get_current_user
from app.dependencies.rag import get_rag_service
from app.dto.chat import (
    ChatQueryRequest,
    ChatQueryResponse,
    ChatSource,
)
from app.models.users import User
from app.services.rag.rag_service import RAGService


router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)

@router.post(
    "/query",
    response_model=ChatQueryResponse,
)
def query_knowledge_base(
    request: ChatQueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    rag_service: RAGService = Depends(get_rag_service),
) -> ChatQueryResponse:

    result = rag_service.answer(
        db=db,
        query=request.query,
        current_user=current_user,
    )

    sources: list[ChatSource] = []

    seen_document_ids: set[int] = set()

    for chunk in result.sources:

        if chunk.document_id in seen_document_ids:
            continue

        seen_document_ids.add(chunk.document_id)

        sources.append(
            ChatSource(
                document_id=chunk.document_id,
                original_filename=chunk.original_filename,
            )
        )

    return ChatQueryResponse(
        query=result.query,
        answer=result.answer,
        sources=sources,
    )