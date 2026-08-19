from __future__ import annotations
from uuid import uuid4
from sqlalchemy.orm import Session

from app.dto.rag_response import RAGResult
from app.services.retrieval.retrieval_service import RetrievalService
from app.services.generation.answer_generation_service import AnswerGenerationService
from app.services.observability.rag_trace import RAGTrace
from app.services.observability.rag_logger import log_rag_trace

class RAGService:

    def __init__(self,*,retrieval_service: RetrievalService,answer_generation_service: AnswerGenerationService):

        self.retrieval_service = retrieval_service
        self.answer_generation_service = (
            answer_generation_service
        )

    def answer(self,*,db: Session,query: str,current_user,trace:RAGTrace|None=None) -> RAGResult:

        if not query or not query.strip():
            raise ValueError(
                "Query cannot be empty."
            )

        normalized_query = query.strip()

        if trace is None:
            trace = RAGTrace(
                request_id=str(uuid4()),
                user_id=current_user.user_id,
                organization_id=current_user.organization_id,
            )

        trace.original_query = normalized_query

        try:
            chunks = self.retrieval_service.retrieve(
                db=db,
                query=normalized_query,
                current_user=current_user,
                trace=trace
            )
    
            if not chunks:
                result = RAGResult(
                    query=normalized_query,
                    answer=(
                        "I could not find enough information "
                        "in the available knowledge base to "
                        "answer this question."
                    ),
                    sources=[],
                )

                trace.finish(status="NO_CONTEXT")
                log_rag_trace(trace)
    
                return result
            
    
            answer = self.answer_generation_service.generate(
                query=normalized_query,
                chunks=chunks,
                trace=trace
            )

            trace.finish(status="SUCCESS")
            log_rag_trace(trace)
    
            return RAGResult(
                query=normalized_query,
                answer=answer,
                sources=chunks,
            )

        except Exception:
            trace.finish(status="FAILED")
            log_rag_trace(trace)
            raise
        