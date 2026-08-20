from functools import lru_cache

from app.dependencies.rag import (
    get_rag_service,
    get_gemini_client,
)

from app.agents.critic_agent import (
    CriticAgent,
)

from app.agents.graph.graph import (
    build_rag_agent_graph,
)


@lru_cache(maxsize=1)
def get_critic_agent() -> CriticAgent:

    return CriticAgent(
        llm_client=get_gemini_client(),
    )


@lru_cache(maxsize=1)
def get_agentic_rag_graph():

    return build_rag_agent_graph(
        rag_service=get_rag_service(),
        critic_agent=get_critic_agent(),
        max_retries=2,
    )