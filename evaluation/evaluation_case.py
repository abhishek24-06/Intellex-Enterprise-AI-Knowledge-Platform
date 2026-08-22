from __future__ import annotations

from pydantic import BaseModel


class EvaluationCase(BaseModel):
    id: str
    category: str
    user_input: str
    reference: str