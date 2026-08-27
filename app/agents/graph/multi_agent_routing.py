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

    retry_count = state.get(
    "retry_count",
    0,
)

    max_retries = state.get(
        "max_retries",
        2,
    )
    
    if retry_count >= max_retries:
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

    retry_count = state.get(
        "retry_count",
        0,
    )

    max_retries = state.get(
        "max_retries",
        2,
    )

    if retry_count >= max_retries:
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


def route_after_synthesis(
    state: MultiAgentState,
) -> str:
    """
    Route after synthesis based on the agent route.
    - KNOWLEDGE/DATABASE: Skip critic (already validated internally or low value)
    - HYBRID: Run critic to validate combined synthesis
    """
    route = state.get("route")

    if route in ("KNOWLEDGE", "DATABASE"):
        return "finalize"

    if route == "HYBRID":
        return "critic"

    # CONVERSATIONAL already ends at END, shouldn't reach here
    # But handle gracefully
    return "finalize"


def route_after_retry_agent(
    state: MultiAgentState,
) -> str:
    """
    Route after a retry agent (knowledge_agent or database_agent) completes.
    - For single-agent routes (KNOWLEDGE/DATABASE): go directly to finalize (synthesis is passthrough)
    - For HYBRID: go to synthesis to combine results, then critic
    """
    route = state.get("route")
    retry_target = state.get("retry_target")

    # If we're in a retry, check what was retried
    if retry_target in ("KNOWLEDGE", "DATABASE"):
        # Single-agent retry: the other agent's result is already in state
        # synthesis will passthrough, so go directly to finalize
        return "finalize"

    if retry_target == "BOTH":
        # Hybrid retry: both agents ran, need synthesis then critic
        return "synthesis"

    # Fallback: use original route
    if route in ("KNOWLEDGE", "DATABASE"):
        return "finalize"
    if route == "HYBRID":
        return "synthesis"

    return "finalize"


def route_after_agent(
    state: MultiAgentState,
) -> str:
    """
    Route after knowledge_agent or database_agent completes.
    Handles both initial run and retry run.
    """
    route = state.get("route")
    retry_target = state.get("retry_target")

    # If we're in a retry, use retry_target to determine routing
    if retry_target:
        return route_after_retry_agent(state)

    # Initial run routing
    if route == "HYBRID":
        return "synthesis"
    if route in ("KNOWLEDGE", "DATABASE"):
        return "synthesis"

    return "finalize"