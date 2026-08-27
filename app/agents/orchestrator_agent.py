from __future__ import annotations

from enum import Enum
import json
import re

from pydantic import BaseModel, Field


class AgentRoute(str, Enum):
    KNOWLEDGE = "KNOWLEDGE"
    DATABASE = "DATABASE"
    HYBRID = "HYBRID"
    CONVERSATIONAL = "CONVERSATIONAL"

class OrchestratorDecision(BaseModel):
    route: AgentRoute
    knowledge_query: str | None = None
    database_query: str | None = None
    reason: str

class OrchestratorAgent:
    SYSTEM_PROMPT = """\
You are the Orchestrator Agent for Intellex.

Your responsibility is ONLY to determine which specialist
should handle the user's query.

Available routes:

1. KNOWLEDGE
   Use for questions answered from enterprise documents,
   policies, SOPs, technical documents, reports, procedures,
   or the organization's knowledge base.

2. DATABASE
   Use for questions about users, emails, departments,
   teams, organizations, roles, or other structured
   enterprise data.

3. HYBRID
   Use when the question genuinely requires both:
   - enterprise database information
   - enterprise document knowledge

4. CONVERSATIONAL
   Use for greetings, thanks, farewells, and simple
   conversational messages that do not require enterprise
   knowledge or database information.

Examples:

"Hi"
→ CONVERSATIONAL

"Hello"
→ CONVERSATIONAL

"Thanks"
→ CONVERSATIONAL

"Good morning"
→ CONVERSATIONAL

Examples:

"What is my email?"
→ DATABASE

"What department am I in?"
→ DATABASE

""What should an operator check before changing an internal service?""
→ KNOWLEDGE

"What is our password policy?"
→ KNOWLEDGE

"What is my department and what does its access policy say?"
→ HYBRID

"What team is Rahul in and what does that team's SOP say?"
→ HYBRID

Return ONLY valid JSON:

{
    "route": "KNOWLEDGE | DATABASE | HYBRID | CONVERSATIONAL",
    "knowledge_query": "... or null",
    "database_query": "... or null",
    "reason": "..."
}"""

    CONVERSATIONAL_PATTERNS = [
        r"^\s*(hi|hello|hey|hiya|howdy)[\s!.]*$",
        r"^\s*(good\s+(morning|afternoon|evening))[\s!.]*$",
        r"^\s*(thanks|thank\s+you|thx|ty)[\s!.]*$",
        r"^\s*(bye|goodbye|see\s+you(\s+later)?|catch\s+you\s+later|take\s+care)[\s!.]*$",
        r"^\s*(hi|hello|hey)[\s,]+(thanks|thank\s+you)[\s!.]*$",
        r"^\s*(bye|goodbye)[\s,]+(thanks|thank\s+you)[\s!.]*$",
        r"^\s*(thanks|thank\s+you)[\s,]+(bye|goodbye|see\s+you)[\s!.]*$",
        r"^\s*(how\s+are\s+you|what'?s\s+up|how'?s\s+(it\s+going|your\s+day))\??\s*$",
        r"^\s*(ok|okay|sure|alright)[\s!.]*$",
        r"^\s*(welcome)[\s!.]*$",
    ]

    def __init__(self, *, llm_client):
            self.llm_client = llm_client
            self._compiled_patterns = [re.compile(p, re.IGNORECASE) for p in self.CONVERSATIONAL_PATTERNS]

    @staticmethod
    def _parse_json(
        raw_response: str,
    ) -> dict:

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

            cleaned = "\n".join(
                lines
            ).strip()

        try:
            return json.loads(cleaned)

        except json.JSONDecodeError as exc:
            raise RuntimeError(
                "Orchestrator returned invalid JSON: "
                f"{cleaned!r}"
            ) from exc

    def _is_conversational(self, query: str) -> bool:
        normalized = query.strip()
        for pattern in self._compiled_patterns:
            if pattern.match(normalized):
                return True
        return False

    def route(
        self,
        *,
        query: str,
    ) -> OrchestratorDecision:

        if not query or not query.strip():
            raise ValueError(
                "Query cannot be empty."
            )

        normalized_query = query.strip()

        if self._is_conversational(normalized_query):
            return OrchestratorDecision(
                route=AgentRoute.CONVERSATIONAL,
                knowledge_query=None,
                database_query=None,
                reason="Fast-path: detected conversational greeting/thanks/farewell/small-talk pattern",
            )

        raw = self.llm_client.generate(
            system_prompt=self.SYSTEM_PROMPT,
            user_prompt=normalized_query,
            response_format={
                "type": "json_object",
           },
        )

        if not raw or not raw.strip():
            raise RuntimeError(
                "Orchestrator returned "
                "an empty response."
            )

        payload = self._parse_json(raw)

        return OrchestratorDecision.model_validate(
            payload
        )