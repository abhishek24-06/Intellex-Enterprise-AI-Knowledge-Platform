from __future__ import annotations

import json
from typing import Any

from app.services.generation.openrouter_client import (
    OpenRouterClient,
)


class HybridEvaluationResult:

    def __init__(
        self,
        *,
        database_correctness: float,
        document_grounding: float,
        combined_answer_correctness: float,
        reasoning: str,
    ):
        self.database_correctness = (
            database_correctness
        )

        self.document_grounding = (
            document_grounding
        )

        self.combined_answer_correctness = (
            combined_answer_correctness
        )

        self.reasoning = reasoning


class HybridEvaluator:

    SYSTEM_PROMPT = """
You are an evaluation judge for an enterprise multi-agent RAG system.

The system can answer using two evidence channels:

1. DATABASE EVIDENCE
   Structured enterprise information.

2. KNOWLEDGE EVIDENCE
   Retrieved enterprise documents.

Evaluate the final answer against BOTH evidence sources
and the reference answer.

Return ONLY JSON:

{
  "database_correctness": 0.0,
  "document_grounding": 0.0,
  "combined_answer_correctness": 0.0,
  "reasoning": "..."
}

Scores must be between 0 and 1.

database_correctness:
Does the answer correctly use the database evidence?

document_grounding:
Are document-backed claims supported by the retrieved documents?

combined_answer_correctness:
Does the final answer correctly combine both evidence
sources and answer the user's question?

Do not reward unsupported claims.
Do not use outside knowledge.
"""

    def __init__(
        self,
        *,
        llm_client: OpenRouterClient,
    ):
        self.llm_client = llm_client

    def evaluate(
        self,
        *,
        query: str,
        database_evidence: str | None,
        retrieved_contexts: list[str],
        response: str,
        reference: str,
    ) -> HybridEvaluationResult:

        document_context = "\n\n".join(
            retrieved_contexts
        )

        prompt = f"""
USER QUERY:
{query}

DATABASE EVIDENCE:
{database_evidence or "NONE"}

KNOWLEDGE EVIDENCE:
{document_context or "NONE"}

FINAL ANSWER:
{response}

REFERENCE ANSWER:
{reference}
"""

        raw = self.llm_client.generate(
            system_prompt=self.SYSTEM_PROMPT,
            user_prompt=prompt,
        )

        if not raw:
            raise RuntimeError(
                "Hybrid evaluator returned an empty response."
            )

        cleaned = raw.strip()

        if cleaned.startswith("```"):
            lines = cleaned.splitlines()

            if lines:
                lines = lines[1:]

            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]

            cleaned = "\n".join(lines)

        try:
            data: dict[str, Any] = (
                json.loads(cleaned)
            )
        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "Hybrid evaluator returned invalid JSON."
            ) from exc

        return HybridEvaluationResult(
            database_correctness=float(
                data["database_correctness"]
            ),
            document_grounding=float(
                data["document_grounding"]
            ),
            combined_answer_correctness=float(
                data["combined_answer_correctness"]
            ),
            reasoning=str(
                data["reasoning"]
            ),
        )