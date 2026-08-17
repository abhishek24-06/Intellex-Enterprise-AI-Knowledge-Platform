from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.dependencies.auth import get_current_user

from app.models.users import User

from app.dto.retrieval import (
    RetrievalRequest,
    RetrievalResponse,
    RetrievedChunkResponse,
)

from app.services.embedding.bge_m3_embedding_service import (
    BGEM3EmbeddingService,
)

from app.services.reranking.bge_reranker_service import (
    BGERerankerService,
)

from app.services.retrieval.vector_search_repository import (
    VectorSearchRepository,
)

from app.services.retrieval.retrieval_service import (
    RetrievalService,
)


router = APIRouter(
    prefix="/retrieval",
    tags=["Retrieval"],
)


# ======================================================================
# RETRIEVAL DEPENDENCIES
# ======================================================================

embedding_service = BGEM3EmbeddingService()

vector_search_repository = VectorSearchRepository()

reranker_service = BGERerankerService()

retrieval_service = RetrievalService(
    embedding_service=embedding_service,
    vector_search_repository=vector_search_repository,
    reranker_service=reranker_service,
)


# ======================================================================
# SEARCH
# ======================================================================


@router.post(
    "/search",
    response_model=RetrievalResponse,
)
def search(
    request: RetrievalRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Perform authenticated, ACL-aware semantic retrieval.

    Pipeline:

        Query
          ↓
        BGE-M3
          ↓
        ACL-aware pgvector search
          ↓
        BGE reranker
          ↓
        Final RetrievedChunk[]
    """

    results = retrieval_service.retrieve(
        db=db,
        query=request.query,
        current_user=current_user,
    )

    return RetrievalResponse(
        query=request.query,
        results=[
            RetrievedChunkResponse(
                document_id=result.document_id,
                chunk_id=result.chunk_id,
                chunk_index=result.chunk_index,
                chunk_text=result.chunk_text,
                token_count=result.token_count,
                metadata=result.metadata,
                vector_score=result.vector_score,
                rerank_score=result.rerank_score,
            )
            for result in results
        ],
    )