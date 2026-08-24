from __future__ import annotations

from langgraph.types import Send

from app.agents.critic_agent import CriticDecision
from app.agents.graph.state import RAGAgentState
from app.agents.multi_agent_state import MultiAgentState


# ======================================================================
# Multi-Agent Orchestrator Routing
# ======================================================================


def route_after_orchestrator(
    state: MultiAgentState,
) -> str | list[Send]:

    route = state.get(
        "route"
    )

    # --------------------------------------------------------------
    # Knowledge only
    # --------------------------------------------------------------

    if route == "KNOWLEDGE":
        return "knowledge"

    # --------------------------------------------------------------
    # Database only
    # --------------------------------------------------------------

    if route == "DATABASE":
        return "database"

    #Conversation only
    if route == "CONVERSATIONAL":
        return "conversational"

    # --------------------------------------------------------------
    # Hybrid
    #
    # Run Knowledge Agent and Database Agent as separate branches.
    # --------------------------------------------------------------

    if route == "HYBRID":
        return [
            Send(
                "knowledge_agent",
                {
                    **state,
                    "knowledge_query": (
                        state.get("knowledge_query")
                        or state["original_query"]
                    ),
                },
            ),
            Send(
                "database_agent",
                {
                    **state,
                    "database_query": (
                        state.get("database_query")
                        or state["original_query"]
                    ),
                },
            ),
        ]

    raise RuntimeError(
        f"Unknown orchestrator route: {route}"
    )


# ======================================================================
# Original RAG Graph Critic Routing
# ======================================================================


def route_after_critic(
    state: RAGAgentState,
) -> str:

    rag_result = state.get(
        "rag_result"
    )

    if rag_result is None:
        return "finalize"

    # No usable context.
    if not rag_result.sources:
        return "finalize"

    critique = state.get(
        "critique"
    )

    if critique is None:
        return "finalize"

    if (
        critique.decision
        == CriticDecision.ACCEPT
    ):
        return "finalize"

    attempt = state.get(
        "attempt",
        0,
    )

    max_retries = state.get(
        "max_retries",
        2,
    )

    if attempt > max_retries + 1:
        return "finalize"

    return "retry"


# ======================================================================
# Multi-Agent Critic Routing
# ======================================================================


def route_after_multi_agent_critic(
    state: MultiAgentState,
) -> str:

    critique = state.get(
        "critique"
    )

    if critique is None:
        return "finalize"

    if (
        critique.decision
        == CriticDecision.ACCEPT
    ):
        return "finalize"

    attempt = state.get(
        "attempt",
        0,
    )

    max_retries = state.get(
        "max_retries",
        2,
    )

    if attempt > max_retries:
        return "finalize"

    return "retry"

def route_after_retry_target(
    state: MultiAgentState,
) -> str | list[Send]:

    retry_target = state.get(
        "retry_target"
    )

    if retry_target == "KNOWLEDGE":
        return "knowledge"

    if retry_target == "DATABASE":
        return "database"

    if retry_target == "BOTH":

        return [
            Send(
                "knowledge_agent",
                {
                    **state,
                    "knowledge_query": (
                        state.get(
                            "knowledge_query"
                        )
                        or state["original_query"]
                    ),
                },
            ),
            Send(
                "database_agent",
                {
                    **state,
                    "database_query": (
                        state.get(
                            "database_query"
                        )
                        or state["original_query"]
                    ),
                },
            ),
        ]

    raise RuntimeError(
        f"Unknown retry target: {retry_target}"
    )