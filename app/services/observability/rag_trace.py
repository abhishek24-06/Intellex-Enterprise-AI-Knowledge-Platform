from __future__ import annotations

from dataclasses import dataclass, field
from time import perf_counter


@dataclass
class RAGTrace:
    request_id: str | None = None
    user_id: int | None = None
    organization_id: int | None = None
    session_id: int | None = None

    original_query: str | None = None
    retrieval_query: str | None = None

    vector_candidates: int = 0
    reranked_chunks: int = 0

    source_document_ids: list[int] = field(
        default_factory=list
    )

    embedding_latency_ms: float = 0.0
    vector_search_latency_ms: float = 0.0
    reranker_latency_ms: float = 0.0
    generation_latency_ms: float = 0.0
    contextualization_latency_ms: float = 0.0
    total_latency_ms: float = 0.0

    embedding_cache_hits: int = 0
    embedding_cache_misses: int = 0
    retrieval_cache_hit: bool = False

    status: str = "RUNNING"

    _started_at: float = field(
        default_factory=perf_counter,  #Perfomance time counter
        repr=False,
    )

    def finish(self,*,status:str="SUCCESS")->None:

        self.total_latency_ms = (perf_counter() - self._started_at) * 1000 # X 1000 for sec to ms

        self.status = status 