from functools import lru_cache

from app.services.embedding.bge_m3_embedding_service import BGEM3EmbeddingService
from app.services.query_contextualizer import QueryContextualizer
from app.services.reranking.bge_reranker_service import BGERerankerService
from app.services.retrieval.vector_search_repository import VectorSearchRepository
from app.services.retrieval.retrieval_service import RetrievalService
from app.services.generation.answer_generation_service import AnswerGenerationService
from app.services.generation.openrouter_client import OpenRouterClient
from app.services.generation.prompt_builder import RAGPromptBuilder
from app.services.rag.rag_service import RAGService

@lru_cache(maxsize=1)
def get_embedding_service() -> BGEM3EmbeddingService:

    return BGEM3EmbeddingService()

@lru_cache(maxsize=1)
def get_reranker_service() -> BGERerankerService:

    return BGERerankerService()

@lru_cache(maxsize=1)
def get_vector_search_repository() -> VectorSearchRepository:

    return VectorSearchRepository()


@lru_cache(maxsize=1)
def get_retrieval_service() -> RetrievalService:

    return RetrievalService(
        embedding_service=get_embedding_service(),
        vector_search_repository=(
            get_vector_search_repository()
        ),
        reranker_service=get_reranker_service(),
    )

@lru_cache(maxsize=1)
def get_openrouter_client() -> OpenRouterClient:

    return OpenRouterClient()

@lru_cache(maxsize=1)
def get_answer_generation_service() -> (
    AnswerGenerationService
):

    return AnswerGenerationService(
        llm_client=get_openrouter_client(),
        prompt_builder=RAGPromptBuilder(),
    )

@lru_cache(maxsize=1)
def get_query_contextualizer() -> QueryContextualizer:

    return QueryContextualizer(
        llm_client=get_openrouter_client(),
    )

@lru_cache(maxsize=1)
def get_rag_service() -> RAGService:

    return RAGService(
        retrieval_service=get_retrieval_service(),
        answer_generation_service=(
            get_answer_generation_service()
        ),
    )