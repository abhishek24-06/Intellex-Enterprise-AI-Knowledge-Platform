from __future__ import annotations
from sqlalchemy.orm import Session
from time import perf_counter
from functools import lru_cache
from dataclasses import dataclass
from typing import Optional
import hashlib
import time

from app.dto.retrieved_chunk import RetrievedChunk
from app.services.embedding.bge_m3_embedding_service import BGEM3EmbeddingService
from app.services.retrieval.vector_search_repository import VectorSearchRepository
from app.services.reranking.bge_reranker_service   import BGERerankerService
from app.services.observability.rag_trace import RAGTrace

class RetrievalService:

    #Orchestrates User Query -> Query Embedding -> ACL Check -> Reranker -> Funal Chunks

    DEFAULT_VECTOR_TOP_K = 20
    DEFAULT_RERANK_TOP_K = 5
    DEFAULT_EMBEDDING_CACHE_SIZE = 128
    DEFAULT_RETRIEVAL_CACHE_SIZE = 64
    DEFAULT_RETRIEVAL_CACHE_TTL_SECONDS = 300  # 5 minutes

    def __init__(self,*,
                embedding_service: BGEM3EmbeddingService,
                vector_search_repository: VectorSearchRepository,
                reranker_service: BGERerankerService,
                vector_top_k: int = DEFAULT_VECTOR_TOP_K,
                rerank_top_k: int = DEFAULT_RERANK_TOP_K,
                embedding_cache_size: int = DEFAULT_EMBEDDING_CACHE_SIZE,
                retrieval_cache_size: int = DEFAULT_RETRIEVAL_CACHE_SIZE,
                retrieval_cache_ttl_seconds: int = DEFAULT_RETRIEVAL_CACHE_TTL_SECONDS,
    ):
        if vector_top_k <= 0:
            raise ValueError("vector_top_k must be greater than zero.")

        if rerank_top_k <= 0:
            raise ValueError("rerank_top_k must be greater than zero.")

        if rerank_top_k > vector_top_k:
            raise ValueError("rerank_top_k cannot be greater than vector_top_k.")

        if embedding_cache_size < 0:
            raise ValueError("embedding_cache_size cannot be negative.")

        if retrieval_cache_size < 0:
            raise ValueError("retrieval_cache_size cannot be negative.")

        if retrieval_cache_ttl_seconds <= 0:
            raise ValueError("retrieval_cache_ttl_seconds must be greater than zero.")

        self.embedding_service = embedding_service
        self.vector_search_repository = vector_search_repository
        self.reranker_service = reranker_service

        self.vector_top_k = vector_top_k
        self.rerank_top_k = rerank_top_k
        self.retrieval_cache_ttl_seconds = retrieval_cache_ttl_seconds

        # Embedding cache: query -> embedding
        self._embedding_cache = lru_cache(maxsize=embedding_cache_size)(self._embed_text_uncached)

        # Retrieval result cache: cache_key -> (timestamp, results)
        self._retrieval_cache: dict[str, tuple[float, list[RetrievedChunk]]] = {}
        self._retrieval_cache_max_size = retrieval_cache_size

    def _embed_text_uncached(self, query: str) -> list[float]:
        """Uncached embedding generation - wrapped by LRU cache."""
        embeddings = self.embedding_service.embed_texts(texts=[query])
        if len(embeddings) != 1:
            raise RuntimeError("Embedding service unexpected number of embeddings.")
        query_vector = embeddings[0]
        if len(query_vector) != 1024:
            raise RuntimeError("Query embedding must contain exactly 1024 dimensions.")
        return query_vector

    def _make_cache_key(
        self,
        query: str,
        current_user,
        vector_top_k: int,
        rerank_top_k: int,
    ) -> str:
        """Generate a cache key for the retrieval request."""
        # Include user org, team, dept for ACL-aware caching
        key_parts = [
            query.strip().lower(),
            str(current_user.organization_id),
            str(current_user.user_id),
            str(getattr(current_user, "team_id", "") or ""),
            str(getattr(current_user, "department_id", "") or ""),
            str(vector_top_k),
            str(rerank_top_k),
        ]
        key_string = "|".join(key_parts)
        # Use hash to keep key size manageable
        return hashlib.sha256(key_string.encode()).hexdigest()[:32]

    def _get_cached_results(self, cache_key: str) -> Optional[list[RetrievedChunk]]:
        """Get cached results if valid (not expired)."""
        if cache_key not in self._retrieval_cache:
            return None
        
        timestamp, results = self._retrieval_cache[cache_key]
        if time.time() - timestamp > self.retrieval_cache_ttl_seconds:
            # Expired - remove
            del self._retrieval_cache[cache_key]
            return None
        
        return results

    def _cache_results(self, cache_key: str, results: list[RetrievedChunk]) -> None:
        """Cache results with timestamp, evicting oldest if at capacity."""
        # Simple LRU eviction if at capacity
        if len(self._retrieval_cache) >= self._retrieval_cache_max_size:
            # Remove oldest entry
            oldest_key = min(self._retrieval_cache.keys(), key=lambda k: self._retrieval_cache[k][0])
            del self._retrieval_cache[oldest_key]
        
        self._retrieval_cache[cache_key] = (time.time(), results)

    def _clear_expired_cache(self) -> int:
        """Clear expired cache entries. Returns count of cleared entries."""
        now = time.time()
        expired_keys = [
            k for k, (ts, _) in self._retrieval_cache.items()
            if now - ts > self.retrieval_cache_ttl_seconds
        ]
        for k in expired_keys:
            del self._retrieval_cache[k]
        return len(expired_keys)

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

        # Clean up expired cache entries periodically
        self._clear_expired_cache()

        # Generate cache key and check cache
        cache_key = self._make_cache_key(query, current_user, vector_limit, rerank_limit)
        cached_results = self._get_cached_results(cache_key)

        if cached_results is not None:
            trace.retrieval_cache_hit = True
            trace.vector_candidates = len(cached_results)
            trace.reranked_chunks = len(cached_results)
            return cached_results

        trace.retrieval_cache_hit = False

        embedding_started = perf_counter()

        # Use cached embedding (LRU cache on _embed_text_uncached)
        query_vector = self._embedding_cache(query)

        trace.embedding_latency_ms = (perf_counter() - embedding_started) * 1000

        # Track embedding cache performance
        cache_info = self._embedding_cache.cache_info()
        trace.embedding_cache_hits = cache_info.hits
        trace.embedding_cache_misses = cache_info.misses

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

        # Cache the results
        self._cache_results(cache_key, final_results)

        return final_results

