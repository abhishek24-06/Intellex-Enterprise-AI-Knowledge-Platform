from __future__ import annotations
from dataclasses import dataclass

from app.dto.retrieved_chunk import RetrievedChunk


@dataclass
class RAGResult:

    query: str
    answer: str
    sources: list[RetrievedChunk]