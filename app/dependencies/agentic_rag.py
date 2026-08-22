from __future__ import annotations

from functools import lru_cache

from app.agents.critic_agent import CriticAgent
from app.agents.database_agent import EnterpriseDataAgent
from app.agents.graph.graph import build_multi_agent_graph
from app.agents.orchestrator_agent import OrchestratorAgent
from app.services.agentic_rag_service import AgenticRAGService
from app.services.generation.openrouter_client import OpenRouterClient
from app.services.generation.openrouter_models import get_openrouter_chat_model
from app.services.rag.rag_service import RAGService
from app.dependencies.rag import get_rag_service

# GENERATION CLIENT

@lru_cache(maxsize=1)
def get_openrouter_generation_client() -> (
    OpenRouterClient
):

    return OpenRouterClient()

# ORCHESTRATOR

@lru_cache(maxsize=1)
def get_orchestrator_agent() -> (
    OrchestratorAgent
):

    return OrchestratorAgent(
        llm_client=(
            get_openrouter_generation_client()
        ),
    )

# CRITIC

@lru_cache(maxsize=1)
def get_critic_agent() -> CriticAgent:

    return CriticAgent(
        llm_client=(
            get_openrouter_generation_client()
        ),
    )

# DATABASE AGENT

@lru_cache(maxsize=1)
def get_database_agent() -> (
    EnterpriseDataAgent
):

    return EnterpriseDataAgent(
        model=get_openrouter_chat_model(
            temperature=0.0,
        ),
    )

# SYNTHESIS MODEL

@lru_cache(maxsize=1)
def get_synthesis_client() -> (
    OpenRouterClient
):

    return get_openrouter_generation_client()

# AGENTIC RAG SERVICE

@lru_cache(maxsize=1)
def get_agentic_rag_service() -> (
    AgenticRAGService
):

    rag_service: RAGService = (
        get_rag_service()
    )

    graph = build_multi_agent_graph(
        orchestrator=(
            get_orchestrator_agent()
        ),
        rag_service=rag_service,
        data_agent=get_database_agent(),
        critic_agent=get_critic_agent(),
        llm_client=get_synthesis_client(),
    )

    return AgenticRAGService(
        graph=graph,
    )