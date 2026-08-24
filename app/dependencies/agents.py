from functools import lru_cache

from app.agents.critic_agent import CriticAgent
from app.agents.database_agent import EnterpriseDataAgent
from app.agents.orchestrator_agent import OrchestratorAgent
from app.agents.graph.graph import build_multi_agent_graph

from app.dependencies.rag import get_rag_service

from app.services.generation.llm_factory import get_chat_model
from app.services.generation.provider_client import ProviderLLMClient


@lru_cache(maxsize=1)
def get_orchestrator_agent() -> OrchestratorAgent:
    return OrchestratorAgent(
        llm_client=ProviderLLMClient(),
    )


@lru_cache(maxsize=1)
def get_critic_agent() -> CriticAgent:
    return CriticAgent(
        llm_client=ProviderLLMClient(),
    )


@lru_cache(maxsize=1)
def get_database_agent() -> EnterpriseDataAgent:

    model = get_chat_model(
        temperature=0,
    )

    return EnterpriseDataAgent(
        model=model,
    )


@lru_cache(maxsize=1)
def get_multi_agent_graph():
    return build_multi_agent_graph(
        orchestrator=get_orchestrator_agent(),
        rag_service=get_rag_service(),
        data_agent=get_database_agent(),
        critic_agent=get_critic_agent(),
        llm_client=ProviderLLMClient(),
    )