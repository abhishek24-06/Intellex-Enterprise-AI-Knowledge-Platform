from __future__ import annotations

from langgraph.runtime import Runtime

from app.agents.graph.state import (
    RAGAgentState,
    RAGGraphContext,
)
from app.agents.critic_agent import CriticAgent
from app.agents.multi_agent_state import MultiAgentState
from app.services.rag.rag_service import RAGService
from app.agents.orchestrator_agent import OrchestratorAgent


# ======================================================================
# ORIGINAL RAG GRAPH NODES
# ======================================================================
# These belong to the original Agent 1 -> Agent 2 self-correcting
# RAG graph. Keep them separate from the new multi-agent graph nodes.
# ======================================================================


# ----------------------------------------------------------------------
# Agent 1 — Original Knowledge Agent
# ----------------------------------------------------------------------


def knowledge_agent_node(
    state: RAGAgentState,
    runtime: Runtime[RAGGraphContext],
    *,
    rag_service: RAGService,
) -> dict:

    query = (
        state.get("retrieval_query")
        or state["original_query"]
    )

    result = rag_service.answer(
        db=runtime.context.db,
        query=query,
        current_user=runtime.context.current_user,
    )

    attempt = state.get(
        "attempt",
        0,
    )

    return {
        "retrieval_query": query,
        "rag_result": result,
        "attempt": attempt + 1,
        "history": [
            *state.get("history", []),
            {
                "node": "knowledge_agent",
                "query": query,
                "attempt": attempt + 1,
            },
        ],
    }


# ----------------------------------------------------------------------
# Agent 2 — Original Critic
# ----------------------------------------------------------------------


def critic_agent_node(
    state: RAGAgentState,
    *,
    critic_agent: CriticAgent,
) -> dict:

    rag_result = state.get(
        "rag_result"
    )

    if rag_result is None:
        raise RuntimeError(
            "Critic Agent requires a RAG result."
        )

    if not rag_result.sources:
        return {
            "critique": None,
            "history": [
                *state.get("history", []),
                {
                    "node": "critic_agent",
                    "decision": "NO_CONTEXT",
                },
            ],
        }

    critique = critic_agent.evaluate(
        query=(
            state.get("retrieval_query")
            or state["original_query"]
        ),
        answer=rag_result.answer,
        chunks=rag_result.sources,
    )

    return {
        "critique": critique,
        "history": [
            *state.get("history", []),
            {
                "node": "critic_agent",
                "decision": critique.decision.value,
                "context_relevance": (
                    critique.context_relevance
                ),
                "faithfulness": (
                    critique.faithfulness
                ),
                "answer_correctness": (
                    critique.answer_correctness
                ),
            },
        ],
    }


# ----------------------------------------------------------------------
# Original Finalize
# ----------------------------------------------------------------------


def finalize_node(
    state: RAGAgentState,
) -> dict:

    rag_result = state.get(
        "rag_result"
    )

    if rag_result is None:
        raise RuntimeError(
            "Cannot finalize without a RAG result."
        )

    return {
        "final_answer": rag_result.answer,
        "history": [
            *state.get("history", []),
            {
                "node": "finalize",
            },
        ],
    }


# ----------------------------------------------------------------------
# Original Retry
# ----------------------------------------------------------------------


def prepare_retry_node(
    state: RAGAgentState,
) -> dict:

    critique = state.get(
        "critique"
    )

    if critique is None:
        raise RuntimeError(
            "Retry requires a critique."
        )

    improved_query = (
        critique.improved_query
    )

    if not improved_query:
        raise RuntimeError(
            "Critic requested retry without "
            "an improved query."
        )

    return {
        "retrieval_query": (
            improved_query.strip()
        ),
        "history": [
            *state.get("history", []),
            {
                "node": "prepare_retry",
                "improved_query": (
                    improved_query.strip()
                ),
            },
        ],
    }


# ======================================================================
# MULTI-AGENT GRAPH NODES
# ======================================================================


# ----------------------------------------------------------------------
# Agent 3 — Database Agent
# ----------------------------------------------------------------------


def database_agent_node(
    state,
    runtime,
    *,
    data_agent,
):
    query = (
        state.get("database_query")
        or state["original_query"]
    )

    result = data_agent.invoke(
        query=query,
        db=runtime.context.db,
        current_user=runtime.context.current_user,
    )

    # IMPORTANT:
    # history uses a reducer in MultiAgentState,
    # so return ONLY the new event.
    return {
        "database_result": result,
        "history": [
            {
                "node": "database_agent",
                "query": query,
            }
        ],
    }


# ----------------------------------------------------------------------
# Agent 4 — Orchestrator
# ----------------------------------------------------------------------


def orchestrator_node(
    state: MultiAgentState,
    *,
    orchestrator: OrchestratorAgent,
) -> dict:

    decision = orchestrator.route(
        query=state["original_query"]
    )

    return {
        "route": decision.route.value,
        "knowledge_query": decision.knowledge_query,
        "database_query": decision.database_query,
        "route_reason": decision.reason,
        "history": [
            {
                "node": "orchestrator",
                "route": decision.route.value,
                "reason": decision.reason,
            }
        ],
    }


# ----------------------------------------------------------------------
# Hybrid Knowledge Branch
# ----------------------------------------------------------------------


def hybrid_knowledge_node(
    state,
    runtime,
    *,
    rag_service,
):
    return multi_agent_knowledge_node(
        state,
        runtime,
        rag_service=rag_service,
    )


# ----------------------------------------------------------------------
# Hybrid Database Branch
# ----------------------------------------------------------------------


def hybrid_database_node(
    state,
    runtime,
    *,
    data_agent,
):
    return database_agent_node(
        state,
        runtime,
        data_agent=data_agent,
    )


# ----------------------------------------------------------------------
# Agent 1 — Multi-Agent Knowledge Node
# ----------------------------------------------------------------------


def multi_agent_knowledge_node(
    state,
    runtime,
    *,
    rag_service,
):
    query = (
        state.get("knowledge_query")
        or state.get("retrieval_query")
        or state["original_query"]
    )

    result = rag_service.answer(
        db=runtime.context.db,
        query=query,
        current_user=runtime.context.current_user,
    )

    attempt = state.get(
        "attempt",
        0,
    ) + 1

    return {
        "knowledge_query": query,
        "retrieval_query": query,
        "rag_result": result,
        "attempt": attempt,
        # ONLY the new event.
        "history": [
            {
                "node": "knowledge_agent",
                "query": query,
                "attempt": attempt,
            }
        ],
    }


# ----------------------------------------------------------------------
# Synthesis
# ----------------------------------------------------------------------


def synthesis_node(
    state,
    *,
    llm_client,
):

    knowledge = state.get(
        "rag_result"
    )

    database = state.get(
        "database_result"
    )

    knowledge_answer = (
        knowledge.answer
        if knowledge is not None
        else ""
    )

    database_answer = (
        database
        or ""
    )

    prompt = f"""\
USER QUERY:
{state["original_query"]}

DATABASE AGENT RESULT:
{database_answer}

KNOWLEDGE AGENT RESULT:
{knowledge_answer}

Combine the available information into one accurate,
concise answer.

Rules:
- Do not invent facts.
- Use the database result only for structured enterprise data.
- Use the knowledge result only for document-backed information.
- If either source is missing information, do not fabricate it.
"""

    answer = llm_client.generate(
        system_prompt=(
            "You are the final synthesis component "
            "of an enterprise multi-agent system."
        ),
        user_prompt=prompt,
    )

    return {
        "final_answer": answer,
        "history": [
            {
                "node": "synthesis",
            }
        ],
    }


# ----------------------------------------------------------------------
# Agent 2 — Multi-Agent Critic
# ----------------------------------------------------------------------


def multi_agent_critic_node(
    state,
    *,
    critic_agent,
):
    """
    Critic for the final synthesized multi-agent answer.

    For the current implementation, the CriticAgent evaluates
    document-backed answers using the retrieved RAG chunks.

    Database-only queries are currently skipped because the
    existing CriticAgent expects retrieved document chunks.
    """

    final_answer = state.get(
        "final_answer"
    )

    if not final_answer:
        raise RuntimeError(
            "Multi-agent critic requires a final answer."
        )

    knowledge = state.get(
        "rag_result"
    )

    if knowledge is None:
        return {
            "critique": None,
            "history": [
                {
                    "node": "multi_agent_critic",
                    "decision": (
                        "SKIPPED_NO_DOCUMENT_CONTEXT"
                    ),
                }
            ],
        }

    chunks = knowledge.sources

    if not chunks:
        return {
            "critique": None,
            "history": [
                {
                    "node": "multi_agent_critic",
                    "decision": (
                        "SKIPPED_NO_DOCUMENT_CONTEXT"
                    ),
                }
            ],
        }

    query = state["original_query"]

    critique = critic_agent.evaluate(
        query=query,
        answer=final_answer,
        chunks=chunks,
    )

    # IMPORTANT:
    # Do not prepend existing history here.
    return {
        "critique": critique,
        "history": [
            {
                "node": "multi_agent_critic",
                "decision": (
                    critique.decision.value
                ),
                "context_relevance": (
                    critique.context_relevance
                ),
                "faithfulness": (
                    critique.faithfulness
                ),
                "answer_correctness": (
                    critique.answer_correctness
                ),
            }
        ],
    }


# ----------------------------------------------------------------------
# Multi-Agent Finalize
# ----------------------------------------------------------------------


def multi_agent_finalize_node(
    state,
) -> dict:

    final_answer = state.get(
        "final_answer"
    )

    if not final_answer:
        raise RuntimeError(
            "Cannot finalize without a final answer."
        )

    return {
        "final_answer": final_answer,
        "history": [
            {
                "node": "finalize",
            }
        ],
    }


# ----------------------------------------------------------------------
# Multi-Agent Retry
# ----------------------------------------------------------------------


def multi_agent_prepare_retry_node(
    state,
) -> dict:

    critique = state.get(
        "critique"
    )

    if critique is None:
        raise RuntimeError(
            "Retry requires a critique."
        )

    improved_query = (
        critique.improved_query
    )

    if not improved_query:
        raise RuntimeError(
            "Critic requested RETRY without "
            "an improved query."
        )

    # IMPORTANT:
    # Do NOT increment attempt here.
    # multi_agent_knowledge_node owns attempt counting.
    return {
        "knowledge_query": (
            improved_query.strip()
        ),
        "retrieval_query": (
            improved_query.strip()
        ),
        "final_answer": None,
        "history": [
            {
                "node": "prepare_retry",
                "improved_query": (
                    improved_query.strip()
                ),
            }
        ],
    }