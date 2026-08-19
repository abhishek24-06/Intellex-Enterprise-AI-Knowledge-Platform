from __future__ import annotations
from sqlalchemy.orm import Session
from time import perf_counter

from app.dto.retrieved_chunk import RetrievedChunk
from app.services.embedding.bge_m3_embedding_service import BGEM3EmbeddingService
from app.services.retrieval.vector_search_repository import VectorSearchRepository
from app.services.reranking.bge_reranker_service   import BGERerankerService
from app.services.observability.rag_trace import RAGTrace

class RetrievalService:

    #Orchestrates User Query -> Query Embedding -> ACL Check -> Reranker -> Funal Chunks

    DEFAULT_VECTOR_TOP_K = 30
    DEFAULT_RERANK_TOP_K = 5

    def __init__(self,*,
                embedding_service: BGEM3EmbeddingService,
                vector_search_repository: VectorSearchRepository,
                reranker_service: BGERerankerService,
                vector_top_k: int = DEFAULT_VECTOR_TOP_K,
                rerank_top_k: int = DEFAULT_RERANK_TOP_K,
    ):
        if vector_top_k <= 0:
            raise ValueError("vector_top_k must be greater than zero.")

        if rerank_top_k <= 0:
            raise ValueError("rerank_top_k must be greater than zero.")

        if rerank_top_k > vector_top_k:
            raise ValueError("rerank_top_k cannot be greater than vector_top_k.")

        self.embedding_service = embedding_service
        self.vector_search_repository = vector_search_repository
        self.reranker_service = reranker_service

        self.vector_top_k = vector_top_k
        self.rerank_top_k = rerank_top_k

    def retrieve(self,*,db: Session,query: str,current_user,vector_top_k: int | None = None,rerank_top_k: int | None = None,trace = None) -> list[RetrievedChunk]:

        if not query or not query.strip():
            raise ValueError("Query cannot be empty.")

        vector_limit = (
            vector_top_k
            if vector_top_k is not None
            else self.vector_top_k
        )

        rerank_limit = (
            rerank_top_k
            if rerank_top_k is not None
            else self.rerank_top_k
        )

        if vector_limit <= 0:
            raise ValueError("vector_top_k must be greater than zero.")

        if rerank_limit <= 0:
            raise ValueError("rerank_top_k must be greater than zero.")

        if rerank_limit > vector_limit:
            raise ValueError("rerank_top_k cannot be greater than vector_top_k.")

        if trace is None:
            trace = RAGTrace()

        trace.retrieval_query = query
        
        embedding_started = perf_counter()
        
        query_embedding = (
            self.embedding_service.embed_texts(
                texts=[query]
            )
        )

        trace.embedding_latency_ms = (perf_counter() - embedding_started) * 1000

        if len(query_embedding) != 1:
            raise RuntimeError("Embedding service unexpected number of embeddings.")

        query_vector = query_embedding[0]

        if len(query_vector) != 1024:
            raise RuntimeError("Query embedding must contain exactly 1024 dimensions.")

        vector_started = perf_counter()

        candidates = (
            self.vector_search_repository.search(
                db=db,
                query_embedding=query_vector,
                current_user=current_user,
                top_k=vector_limit,
            )
        )

        trace.vector_search_latency_ms = (perf_counter() - vector_started) * 1000

        trace.vector_candidates = len(candidates)

        if not candidates:
            return []

        reranker_started = perf_counter()

        final_results = (
            self.reranker_service.rerank(
                query=query,
                chunks=candidates,
                top_k=rerank_limit,
            )
        )

        trace.reranker_latency_ms = (perf_counter() - reranker_started) * 1000

        trace.reranked_chunks = len(final_results)
        
        trace.source_document_ids = list(
            dict.fromkeys(
                chunk.document_id
                for chunk in final_results
            )
        )

        return final_results

