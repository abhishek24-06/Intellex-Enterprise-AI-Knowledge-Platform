from __future__ import annotations

from functools import lru_cache

from langgraph.graph import (
    END,
    START,
    StateGraph,
)

from app.agents.graph.nodes import (
    critic_agent_node,
    finalize_node,
    knowledge_agent_node,
    prepare_retry_node,
)
from app.agents.graph.routing import (
    route_after_critic,
)
from app.agents.graph.state import (
    RAGAgentState,
    RAGGraphContext,
)
from app.agents.critic_agent import CriticAgent

def build_rag_graph_agent(*,rag_service,critic_agent:CriticAgent,max_retries:int = 2):

    if max_retries < 0:
        raise ValueError("max_retries cannot be negative.")

    builder = StateGraph(RAGAgentState, context_schema=RAGGraphContext)

    builder.add_node("knowledge_agent",
                     lambda state, runtime:(  #LangGraph, give me state n runtime, and I'll call knowledge_agent_node() with those plus the rag_service it needs.
                         knowledge_agent_node(
                             state,
                             runtime,
                             rag_service=rag_service
                         )
                     ) )

    builder.add_node("critic_agent",
                     lambda state:(
                         critic_agent_node(
                             state,
                             critic_agent=critic_agent
                         )
                     ))

    builder.add_node("prepare_retry",
                    prepare_retry_node,
    )

    builder.add_node("finalize",
                     finalize_node)

    builder.add_edge(START,
                     "knowledge_agent")

    builder.add_edge("knowledge_agent",
                     "critic_agent")

    builder.add_conditional_edges("critic_agent",
                                  route_after_critic,{
                                      "retry": "prepare_retry", # RETURNS ONLY A STRING 
                                      "finalize": "finalize" #RUNS FINALIZE NODE
                                  }
                                )

    builder.add_edge("prepare_retry",
                     "knowledge_agent")

    builder.add_edge("finalize",
                     END)

    return builder.compile()