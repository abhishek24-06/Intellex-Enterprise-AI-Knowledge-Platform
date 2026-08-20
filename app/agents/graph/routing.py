from __future__ import annotations

from app.agents.critic_agent import CriticDecision
from app.agents.graph.state import RAGAgentState

def route_after_critic(state: RAGAgentState) -> str:

    rag_result = state.get("rag_result")

    if rag_result is None:
        return "finalize"

    # No usable context.
    # Don't loop infinitely trying to fix an impossible result.
    if not rag_result.sources:
        return "finalize"

    critique = state.get("critique")

    if critique is None:
        return "finalize"

    if (
        critique.decision
        == CriticDecision.ACCEPT
    ):
        return "finalize"

    attempt = state.get("attempt", 0)
    max_retries = state.get("max_retries", 2)

    if attempt >= max_retries + 1:
        return "finalize"

    return "retry"