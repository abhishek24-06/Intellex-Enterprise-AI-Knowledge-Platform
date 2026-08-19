from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from sqlalchemy.orm import Session

from app.evaluation.metrics import (
    hit_at_k,
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
)
from app.evaluation.models import (
    EvaluationCase,
    RetrievalEvaluationResult,
)
from app.services.retrieval.retrieval_service import (
    RetrievalService,
)


@dataclass
class EvaluationSummary:
    total_cases: int
    average_hit_at_k: float
    average_precision_at_k: float
    average_recall_at_k: float
    average_mrr: float
    results: list[RetrievalEvaluationResult]


class RetrievalEvaluationRunner:
    """
    Runs deterministic retrieval evaluation.

    The runner evaluates retrieval only.
    LLM answer generation is intentionally excluded.
    """

    def __init__(
        self,
        *,
        retrieval_service: RetrievalService,
        top_k: int = 5,
    ):
        if top_k <= 0:
            raise ValueError(
                "top_k must be greater than zero."
            )

        self.retrieval_service = retrieval_service
        self.top_k = top_k

    @staticmethod
    def _unique_document_ids(
        chunks,
    ) -> list[int]:
        """
        Convert chunk-level retrieval results into
        document-level ranking while preserving order.
        """

        seen: set[int] = set()
        document_ids: list[int] = []

        for chunk in chunks:

            document_id = chunk.document_id

            if document_id in seen:
                continue

            seen.add(document_id)
            document_ids.append(document_id)

        return document_ids

    def evaluate_case(
        self,
        *,
        db: Session,
        current_user,
        case: EvaluationCase,
    ) -> RetrievalEvaluationResult:

        chunks = self.retrieval_service.retrieve(
            db=db,
            query=case.query,
            current_user=current_user,
            vector_top_k=self.top_k * 6,
            rerank_top_k=self.top_k,
        )

        retrieved_document_ids = (
            self._unique_document_ids(chunks)
            [: self.top_k]
        )

        return RetrievalEvaluationResult(
            query=case.query,
            retrieved_document_ids=(
                retrieved_document_ids
            ),
            hit_at_k=hit_at_k(
                retrieved_document_ids,
                case.relevant_document_ids,
            ),
            precision_at_k=precision_at_k(
                retrieved_document_ids,
                case.relevant_document_ids,
            ),
            recall_at_k=recall_at_k(
                retrieved_document_ids,
                case.relevant_document_ids,
            ),
            reciprocal_rank=reciprocal_rank(
                retrieved_document_ids,
                case.relevant_document_ids,
            ),
        )

    def evaluate(
        self,
        *,
        db: Session,
        current_user,
        cases: Iterable[EvaluationCase],
    ) -> EvaluationSummary:

        cases = list(cases)

        if not cases:
            raise ValueError(
                "Evaluation dataset cannot be empty."
            )

        results = [
            self.evaluate_case(
                db=db,
                current_user=current_user,
                case=case,
            )
            for case in cases
        ]

        count = len(results)

        return EvaluationSummary(
            total_cases=count,
            average_hit_at_k=(
                sum(
                    result.hit_at_k
                    for result in results
                )
                / count
            ),
            average_precision_at_k=(
                sum(
                    result.precision_at_k
                    for result in results
                )
                / count
            ),
            average_recall_at_k=(
                sum(
                    result.recall_at_k
                    for result in results
                )
                / count
            ),
            average_mrr=(
                sum(
                    result.reciprocal_rank
                    for result in results
                )
                / count
            ),
            results=results,
        )