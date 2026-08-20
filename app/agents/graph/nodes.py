from __future__ import annotations

from langgraph.runtime import Runtime

from app.agents.graph.state import RAGAgentState,RAGGraphContext
from app.agents.critic_agent import CriticAgent
from app.services.rag.rag_service import RAGService

#Agent 1
def knowledge_agent_node(state:RAGAgentState,runtime:Runtime[RAGGraphContext],*,rag_service: RAGService)->dict:

    query = (state.get("retrieval_query") or state["original_query"])

    result = rag_service.answer(db=runtime.context.db,
                                query=query,
                                current_user=runtime.context.current_user)

    attempt = state.get("attempt",0)

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

#Agent Node 2
def critic_agent_node(state:RAGAgentState,*,critic_agent:CriticAgent)->dict:

    rag_result = state.get("rag_result")

    if rag_result is None:
        raise RuntimeError("Critic Agent requires a RAG result.")

    if not rag_result.sources:
        return{
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
        answer = rag_result.answer,
        chunks = rag_result.sources
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
                "faithfulness": critique.faithfulness,
                "answer_correctness": (
                    critique.answer_correctness
                ),
            },
        ],
    }

def finalize_node(state: RAGAgentState,) -> dict:

    rag_result = state.get("rag_result")

    if rag_result is None:
        raise RuntimeError("Cannot finalize without a RAG result.")

    return{
        "final_answer": rag_result.answer,
        "history":[
            *state.get("history",[]),
            {
                "node": "finalize"
            }
        ]
    }

def prepare_retry_node(state:RAGAgentState)->dict:

    critique = state.get("critique")

    if critique is None:
        raise RuntimeError("Retry requires a critique.")

    improved_query = (critique.improved_query)

    if not improved_query:
        raise RuntimeError("Critic requested retry without an improved query.")

    return {
        "retrieval_query": improved_query.strip(),
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
