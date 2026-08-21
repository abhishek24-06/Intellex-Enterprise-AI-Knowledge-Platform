from __future__ import annotations

from enum import Enum
import json

from pydantic import BaseModel, Field


class AgentRoute(str, Enum):
    KNOWLEDGE = "KNOWLEDGE"
    DATABASE = "DATABASE"
    HYBRID = "HYBRID"

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
    "route": "KNOWLEDGE | DATABASE | HYBRID",
    "knowledge_query": "... or null",
    "database_query": "... or null",
    "reason": "..."
}"""

def __init__(self,*,llm_client):
    self.llm_client = llm_client

def route(self,*,query:str)->OrchestratorDecision:

    if not query or not query.strip():
            raise ValueError("Query cannot be empty.")

    raw = self.llm_client.generate(
            system_prompt=self.SYSTEM_PROMPT,
            user_prompt=query.strip()
        )

    if not raw or not raw.strip():
        raise RuntimeError("Orchestrator returned an empty response.")

    try:
        payload = json.loads(raw.strip())
    except json.JSONDecodeError as exc:
        raise RuntimeError("Orchestrator returned invalid JSON.") from exc

    return OrchestratorDecision.model_validate(payload)