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

def _is_useful_retry_query(
    improved_query: str,
    previous_query: str | None,
) -> bool:

    if not improved_query or not improved_query.strip():
        return False

    improved = improved_query.strip().lower()

    generic_queries = {
        "retrieve the relevant enterprise information again.",
        "retrieve the relevant information again.",
        "try again.",
        "retry the query.",
        "search again.",
        "retrieve the information again.",
    }

    if improved in generic_queries:
        return False

    if (
        previous_query
        and improved == previous_query.strip().lower()
    ):
        return False

    return True

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

    route = state.get("route")

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

    # Single-agent routes: bypass LLM synthesis, pass through the answer directly
    if route == "KNOWLEDGE":
        if knowledge is None or not knowledge_answer:
            raise RuntimeError("KNOWLEDGE route requires a RAG result with answer.")
        return {
            "final_answer": knowledge_answer,
            "history": [
                {
                    "node": "synthesis",
                    "mode": "passthrough_knowledge",
                }
            ],
        }

    if route == "DATABASE":
        if not database_answer:
            raise RuntimeError("DATABASE route requires a database result.")
        return {
            "final_answer": database_answer,
            "history": [
                {
                    "node": "synthesis",
                    "mode": "passthrough_database",
                }
            ],
        }

    # HYBRID route: use LLM to synthesize both sources
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
                "mode": "llm_synthesis",
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
    Evaluate the synthesized answer against all evidence
    available to the multi-agent system.
    """

    final_answer = state.get(
        "final_answer"
    )

    if not final_answer:
        raise RuntimeError(
            "Multi-agent critic requires a final answer."
        )

    # --------------------------------------------------------------
    # Knowledge evidence
    # --------------------------------------------------------------

    rag_result = state.get(
        "rag_result"
    )

    chunks = (
        rag_result.sources
        if rag_result is not None
        else []
    )

    # --------------------------------------------------------------
    # Database evidence
    # --------------------------------------------------------------

    database_result = state.get(
        "database_result"
    )

    # --------------------------------------------------------------
    # At least one specialist must have produced evidence.
    # --------------------------------------------------------------

    if (
        not chunks
        and not database_result
    ):
        return {
            "critique": None,
            "retry_target": None,
            "history": [
                {
                    "node": "multi_agent_critic",
                    "decision": (
                        "SKIPPED_NO_EVIDENCE"
                    ),
                }
            ],
        }

    # --------------------------------------------------------------
    # Critic evaluation
    # --------------------------------------------------------------

    critique = critic_agent.evaluate(
        query=state["original_query"],
        answer=final_answer,
        chunks=chunks,
        database_result=database_result,
    )

    return {
        "critique": critique,
        "retry_target": (
            critique.retry_target.value
            if critique.retry_target
            else None
        ),
        "history": [
            {
                "node": "multi_agent_critic",
                "decision": (
                    critique.decision.value
                ),
                "retry_target": (
                    critique.retry_target.value
                    if critique.retry_target
                    else None
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

    retry_target = (
        critique.retry_target
    )

    if retry_target is None:
        raise RuntimeError(
            "Retry requires a retry target."
        )

    if not improved_query:
        raise RuntimeError(
            "Retry requires an improved query."
        )

    # --------------------------------------------------------------
    # Retry counter
    # --------------------------------------------------------------

    current_retry_count = state.get(
        "retry_count",
        0,
    )

    max_retries = state.get(
        "max_retries",
        2,
    )

    next_retry_count = (
        current_retry_count + 1
    )

    # --------------------------------------------------------------
    # Prepare retry
    # --------------------------------------------------------------

    # Preserve existing results for non-targeted agents
    # Only clear final_answer and the targeted agent's result
    update: dict = {
        "max_retries": max_retries,
        "retry_target": retry_target.value,
        "retry_count": next_retry_count,
        "final_answer": None,
        # Don't clear history - let reducer append
    }

    # Clear the targeted agent's result so it gets recomputed
    if retry_target.value in {"KNOWLEDGE", "BOTH"}:
        update["rag_result"] = None
        update["knowledge_query"] = None
        update["retrieval_query"] = None

    if retry_target.value in {"DATABASE", "BOTH"}:
        update["database_result"] = None
        update["database_query"] = None

    # --------------------------------------------------------------
    # Knowledge retry
    # --------------------------------------------------------------

    if retry_target.value in {
        "KNOWLEDGE",
        "BOTH",
    }:

        previous_query = (
            state.get("knowledge_query")
            or state.get("retrieval_query")
            or state.get("original_query")
        )

        if _is_useful_retry_query(
            improved_query,
            previous_query,
        ):
            knowledge_query = (
                improved_query.strip()
            )
        else:
            knowledge_query = (
                previous_query.strip()
                if previous_query
                else improved_query.strip()
            )

        update["knowledge_query"] = (
            knowledge_query
        )

        update["retrieval_query"] = (
            knowledge_query
        )

    # --------------------------------------------------------------
    # Database retry
    # --------------------------------------------------------------

    if retry_target.value in {
        "DATABASE",
        "BOTH",
    }:

        previous_query = (
            state.get("database_query")
            or state.get("original_query")
        )

        if _is_useful_retry_query(
            improved_query,
            previous_query,
        ):
            database_query = (
                improved_query.strip()
            )
        else:
            database_query = (
                previous_query.strip()
                if previous_query
                else improved_query.strip()
            )

        update["database_query"] = (
            database_query
        )

    return update

def conversational_node(
    state,
    llm_client,
):
    query = (
        state.get("original_query")
        or ""
    ).strip()

    if not query:
        answer = "How can I help you?"

    else:
        system_prompt = """
You are Intellex's conversational assistant.

Your job is to respond naturally to casual conversation.

First, silently determine the user's conversational intent.

Possible intents:

1. GREETING
   Examples:
   - hi
   - hello
   - hey
   - good morning
   - good afternoon
   - good evening
   - hey there
   - what's up

2. THANKS
   Examples:
   - thanks
   - thank you
   - thanks a lot
   - appreciate it
   - you're helpful

3. GOODBYE
   Examples:
   - bye
   - goodbye
   - see you
   - see you later
   - catch you later
   - take care

4. GREETING + THANKS
   Examples:
   - hi, thanks
   - hey, thanks for helping

5. GOODBYE + THANKS
   Examples:
   - goodbye, thanks for the help
   - bye, thanks
   - thanks, goodbye
   - appreciate your help, bye

6. SMALL_TALK
   Examples:
   - how are you?
   - what's up?
   - how's your day?

IMPORTANT RESPONSE RULES:

- If the user is greeting you, greet them back.
- If the user thanks you, acknowledge the thanks.
- If the user is saying goodbye, say goodbye back.
- If the user combines multiple intents, respond to ALL of them naturally.
- If the user says goodbye AND thanks, acknowledge the thanks and say goodbye.
- Do NOT respond with a generic "How can I help you?" when the user is clearly saying goodbye.
- Do NOT introduce yourself unless the user asks who you are.
- Do NOT say "I'm an AI assistant for Intellex" unless the user specifically asks what you are.
- Keep conversational responses short and natural.
- Do not answer enterprise knowledge, database, employee,
  department, team, policy, or technical questions.
- Do not invent information.

Examples:

User: "hi"
Response: "Hi! How can I help you?"

User: "good morning"
Response: "Good morning! How can I help you today?"

User: "hey, how are you?"
Response: "I'm doing well! How can I help you?"

User: "thanks"
Response: "You're welcome!"

User: "thanks a lot for your help"
Response: "You're very welcome!"

User: "bye"
Response: "Goodbye! Take care."

User: "goodbye, thanks for the help"
Response: "You're welcome! Goodbye, and take care."

User: "thanks, see you later"
Response: "You're welcome! See you later."

User: "goodbye, thanks for the help"
Response: "You're welcome! Goodbye, and take care."

Return ONLY the response that should be shown to the user.
Do not return the detected intent.
Do not explain your reasoning.
"""

        answer = llm_client.generate(
            system_prompt=system_prompt,
            user_prompt=query,
        )

    return {
        "final_answer": answer.strip(),
        "rag_result": None,
        "database_result": None,
        "history": [
            *state.get("history", []),
            {
                "node": "conversational_agent",
                "status": "SUCCESS",
            },
        ],
    }