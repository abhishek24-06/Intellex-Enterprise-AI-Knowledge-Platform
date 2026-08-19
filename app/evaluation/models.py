from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class EvaluationCase:
    query: str

    relevant_document_ids: set[int]

    expected_answer_keywords: tuple[str, ...] = ()


@dataclass
class RetrievalEvaluationResult:
    query: str

    retrieved_document_ids: list[int]

    hit_at_k: float
    precision_at_k: float
    recall_at_k: float
    reciprocal_rank: float