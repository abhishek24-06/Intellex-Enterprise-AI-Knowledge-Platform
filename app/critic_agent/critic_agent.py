from __future__ import annotations

import json
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class CriticDecision(str, Enum):
    ACCEPT = "ACCEPT"
    RETRY = "RETRY"


class CriticResult(BaseModel):
    decision : CriticDecision

    context_relevance: float = Field(
        ge=0.0,
        le=1.0
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
    improved_query: str | None = None

class CriticAgent:

    SYSTEM_PROMPT = """\
You are the Critic Agent in an enterprise RAG system.

You evaluate a draft answer produced by another agent.

Evaluate ONLY against the supplied retrieved context.

Your responsibilities:

1. Determine whether the retrieved context is relevant.
2. Determine whether the answer is faithful to the context.
3. Determine whether the answer correctly addresses the user query.
4. Reject unsupported claims.
5. If the answer should be retried, provide a better standalone
   retrieval query.

Return ONLY valid JSON in this exact structure:

{
  "decision": "ACCEPT" or "RETRY",
  "context_relevance": 0.0,
  "faithfulness": 0.0,
  "answer_correctness": 0.0,
  "reason": "...",
  "improved_query": "..." or null
}

Scoring:
0.0 = completely poor
0.5 = partially acceptable
1.0 = excellent

Use RETRY when:
- retrieved context does not sufficiently answer the query
- answer contains unsupported claims
- answer does not actually answer the question
- the query is ambiguous and retrieval can be improved

Use ACCEPT only when the answer is sufficiently grounded and
correct.

Do not invent facts.
"""

    ACCEPT_THRESHOLD = 0.80

    def __init__(self, *, llm_client):
        self.llm_client = llm_client

    @staticmethod
    def _build_context(chunks) -> str:
        sections: list[str] = []

        for index, chunk in enumerate(chunks,start=1):
            sections.append("\n".join(
                    [
                        f"[SOURCE {index}]",
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
    def _parse_json(raw_response:str)-> dict[str,Any]:

        cleaned = raw_response.strip()

        if cleaned.startswith("```"):
            lines = cleaned.splitlines()

            if lines and lines[0].startswith("```"):
                lines = lines[1:]

            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]

            cleaned = "\n".join(lines).strip()

        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise RuntimeError("Critic Agent returned invalid JSON") from exc

    def evaluate(self,*,query:str,answer:str,chunks)->CriticResult:

        if not query or not query.strip():
            raise ValueError("Query cannot be empty.")

        if not answer or not answer.strip():
            raise ValueError("Answer cannot be empty.")

        if not chunks:
            raise ValueError("Critic Agent requires retrieved context.")

        context = self._build_context(chunks)

        user_prompt = f"""\
                USER QUERY:
                {query.strip()}
                
                RETRIEVED CONTEXT:
                {context}
                
                DRAFT ANSWER:
                {answer.strip()}
                """

        raw_response = self.llm_client.generate( #INPUT TO CRITIC AGENT
            system_prompt = self.SYSTEM_PROMPT,  #Send the prompt containnig instruction to follow
            user_prompt = user_prompt   #also Sends query, retrieved chunk ,ans
        )

        if not raw_response or not raw_response.strip():
            raise RuntimeError("Critic Agent returned an empty response.")

        payload = self._parse_json(raw_response)

        result = CriticResult.model_validate(payload)

        if (
        result.decision == CriticDecision.RETRY
        and not result.improved_query
    ):
            raise RuntimeError("Critic Agent requested RETRY without an improved query.")

        return result