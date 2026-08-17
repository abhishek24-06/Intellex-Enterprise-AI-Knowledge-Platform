from dataclasses import dataclass, field
from typing import Any

@dataclass
class RetrievedChunk:

    document_id: int
    chunk_id: int
    chunk_index: int
    chunk_text: str
    token_count: int
    metadata: dict[str, Any] = field(default_factory=dict)
    vector_score: float = 0.0
    rerank_score: float | None = None