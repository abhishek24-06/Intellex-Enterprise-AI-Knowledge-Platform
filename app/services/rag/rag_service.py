from __future__ import annotations

from sqlalchemy.orm import Session

from app.dto.rag_response import RAGResult
from app.services.retrieval.retrieval_service import RetrievalService
from app.services.generation.answer_generation_service import (
    AnswerGenerationService,
)

class RAGService:

    def __init__(self,*,retrieval_service: RetrievalService,answer_generation_service: AnswerGenerationService):

        self.retrieval_service = retrieval_service
        self.answer_generation_service = (
            answer_generation_service
        )

    def answer(self,*,db: Session,query: str,current_user,) -> RAGResult:

        if not query or not query.strip():
            raise ValueError(
                "Query cannot be empty."
            )

        normalized_query = query.strip()

        chunks = self.retrieval_service.retrieve(
            db=db,
            query=normalized_query,
            current_user=current_user,
        )

        if not chunks:
            return RAGResult(
                query=normalized_query,
                answer=(
                    "I could not find enough information "
                    "in the available knowledge base to "
                    "answer this question."
                ),
                sources=[],
            )

        answer = self.answer_generation_service.generate(
            query=normalized_query,
            chunks=chunks,
        )

        return RAGResult(
            query=normalized_query,
            answer=answer,
            sources=chunks,
        )