from __future__ import annotations

import json
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class CriticDecision(str, Enum):
    ACCEPT = "ACCEPT"
    RETRY = "RETRY"


class RetryTarget(str, Enum):
    KNOWLEDGE = "KNOWLEDGE"
    DATABASE = "DATABASE"
    BOTH = "BOTH"


class CriticResult(BaseModel):
    decision: CriticDecision

    context_relevance: float = Field(
        ge=0.0,
        le=1.0,
    )

    faithfulness: float = Field(
        ge=0.0,
        le=1.0,
    )

    answer_correctness: float = Field(
        ge=0.0,
        le=1.0,
    )

    reason: str

    retry_target: RetryTarget | None = None

    improved_query: str | None = None


class CriticAgent:
    """
    Agent 2.

    Evaluates the final synthesized answer against the evidence
    actually supplied by the specialist agents.

    Evidence may come from:

        Knowledge Agent
            -> retrieved document chunks

        Database Agent
            -> structured database result

        Hybrid
            -> both
    """

    ACCEPT_THRESHOLD = 0.80

    SYSTEM_PROMPT = """\
You are the Critic Agent in an enterprise multi-agent system.

Your job is to evaluate the FINAL SYNTHESIZED ANSWER against
the evidence supplied by the specialist agents.

Evidence can come from:

1. KNOWLEDGE AGENT
   Enterprise documents, policies, SOPs, technical documents,
   reports, and retrieved document chunks.

2. DATABASE AGENT
   Structured enterprise information such as users,
   departments, teams, roles, and organizations.

3. BOTH
   When the answer combines information from both sources.

Evaluate:

1. context_relevance
   Does the supplied evidence actually address the user's query?

2. faithfulness
   Is the answer supported by the supplied evidence?
   Penalize unsupported or invented claims.

3. answer_correctness
   Does the final answer correctly answer the user's question?

Return ONLY valid JSON:

{
  "decision": "ACCEPT" or "RETRY",
  "context_relevance": 0.0,
  "faithfulness": 0.0,
  "answer_correctness": 0.0,
  "reason": "...",
  "retry_target": "KNOWLEDGE" | "DATABASE" | "BOTH" | null,
  "improved_query": "..." | null
}

Rules:

- ACCEPT only when the answer is sufficiently supported.
- RETRY when important evidence is missing, irrelevant,
  incorrect, or the answer contains unsupported claims.
- retry_target identifies which specialist should be rerun.
- Use KNOWLEDGE when document retrieval needs improvement.
- Use DATABASE when structured enterprise data needs improvement.
- Use BOTH when both sources need improvement.
- improved_query must be a standalone query suitable for the
  specialist identified by retry_target.
- For ACCEPT, retry_target must be null and improved_query
  must be null.
- For RETRY, retry_target and improved_query must be provided.
- Never invent facts.

Do not return commentary outside the JSON.
"""

    def __init__(self, *, llm_client):
        self.llm_client = llm_client

    # ------------------------------------------------------------------
    # Evidence formatting
    # ------------------------------------------------------------------

    @staticmethod
    def _build_document_evidence(
        chunks,
    ) -> str:

        sections: list[str] = []

        for index, chunk in enumerate(
            chunks,
            start=1,
        ):
            sections.append(
                "\n".join(
                    [
                        f"[DOCUMENT SOURCE {index}]",
                        f"Document ID: {chunk.document_id}",
                        (
                            "Filename: "
                            f"{chunk.original_filename}"
                        ),
                        f"Content: {chunk.chunk_text}",
                    ]
                )
            )

        return "\n\n".join(sections)

    @staticmethod
    def _build_evidence(
        *,
        chunks=None,
        database_result: str | None = None,
    ) -> str:

        sections: list[str] = []

        if chunks:
            document_evidence = (
                CriticAgent._build_document_evidence(
                    chunks
                )
            )

            if document_evidence:
                sections.append(
                    "KNOWLEDGE AGENT EVIDENCE:\n"
                    + document_evidence
                )

        if database_result:
            sections.append(
                "DATABASE AGENT EVIDENCE:\n"
                + database_result.strip()
            )

        return "\n\n".join(sections)

    # ------------------------------------------------------------------
    # JSON parser
    # ------------------------------------------------------------------

    @staticmethod
    def _parse_json(
        raw_response: str,
    ) -> dict[str, Any]:

        cleaned = raw_response.strip()

        if cleaned.startswith("```"):
            lines = cleaned.splitlines()

            if (
                lines
                and lines[0].startswith("```")
            ):
                lines = lines[1:]

            if (
                lines
                and lines[-1].strip() == "```"
            ):
                lines = lines[:-1]

            cleaned = "\n".join(lines).strip()

        try:
            return json.loads(cleaned)

        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "Critic Agent returned invalid JSON."
            ) from exc

    # ------------------------------------------------------------------
    # Evaluation
    # ------------------------------------------------------------------

    def evaluate(
        self,
        *,
        query: str,
        answer: str,
        chunks=None,
        database_result: str | None = None,
    ) -> CriticResult:

        if not query or not query.strip():
            raise ValueError(
                "Query cannot be empty."
            )

        if not answer or not answer.strip():
            raise ValueError(
                "Answer cannot be empty."
            )

        evidence = self._build_evidence(
            chunks=chunks,
            database_result=database_result,
        )

        if not evidence:
            raise ValueError(
                "Critic Agent requires at least one "
                "evidence source."
            )

        user_prompt = f"""\
USER QUERY:
{query.strip()}

EVIDENCE:
{evidence}

FINAL SYNTHESIZED ANSWER:
{answer.strip()}
"""

        raw_response = self.llm_client.generate(
            system_prompt=self.SYSTEM_PROMPT,
            user_prompt=user_prompt,
        )

        if (
            not raw_response
            or not raw_response.strip()
        ):
            raise RuntimeError(
                "Critic Agent returned an empty response."
            )

        payload = self._parse_json(
            raw_response
        )

        result = CriticResult.model_validate(
            payload
        )

        should_retry = (
            result.context_relevance < self.ACCEPT_THRESHOLD
            or result.faithfulness < self.ACCEPT_THRESHOLD
            or result.answer_correctness < self.ACCEPT_THRESHOLD
        )


        if should_retry:

            # The critic identified a quality problem.
            # A retry must specify where the graph should retry.
            if result.retry_target is None:
                raise RuntimeError(
                    "Critic Agent identified a low-quality answer "
                    "but did not specify retry_target. "
                    f"reason={result.reason!r}"
                )
        
            if (
                not result.improved_query
                or not result.improved_query.strip()
            ):
                raise RuntimeError(
                    "Critic Agent identified a low-quality answer "
                    "but did not provide improved_query. "
                    f"retry_target={result.retry_target.value}"
                )
        
            result.decision = CriticDecision.RETRY
        
        else:
        
            result.decision = CriticDecision.ACCEPT
        
            result.retry_target = None
            result.improved_query = None
        
        return result