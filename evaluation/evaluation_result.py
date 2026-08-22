from __future__ import annotations

from pydantic import BaseModel


class RAGEvaluationResult(BaseModel):
    question_id: str
    category: str

    faithfulness: float | None = None
    context_recall: float | None = None
    factual_correctness: float | None = None
    response_relevancy: float | None = None

    route_correct: bool | None = None