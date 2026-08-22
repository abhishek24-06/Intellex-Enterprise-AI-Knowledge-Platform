from functools import lru_cache

from app.agents.graph.graph import (
    build_multi_agent_graph,
)

from app.agents.critic_agent import (
    CriticAgent
)

from app.agents.database_agent import (
    EnterpriseDataAgent
)

from app.agents.orchestrator_agent import (
    OrchestratorAgent
)

from app.dependencies.agents import (
    get_gemini_client
)

from langchain_google_genai import ChatGoogleGenerativeAI

from app.dependencies.rag import (
    get_rag_service
)

from app.services.agentic_rag_service import (
    AgenticRAGService,
)


@lru_cache(maxsize=1)
def get_agentic_rag_service() -> AgenticRAGService:

    # --------------------------------------------------------------
    # Shared Gemini client
    # --------------------------------------------------------------

    gemini_client = get_gemini_client()

    # --------------------------------------------------------------
    # Agent 4 — Orchestrator
    # --------------------------------------------------------------

    orchestrator = OrchestratorAgent(
        llm_client=gemini_client,
    )

    # --------------------------------------------------------------
    # Agent 2 — Critic
    # --------------------------------------------------------------

    critic = CriticAgent(
        llm_client=gemini_client,
    )

    # --------------------------------------------------------------
    # Agent 3 — Database Agent
    # --------------------------------------------------------------

    database_model = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0
)

    database_agent = EnterpriseDataAgent(
        model=database_model
    )

    # --------------------------------------------------------------
    # Existing Agent 1 RAG Service
    # --------------------------------------------------------------

    rag_service = get_rag_service()

    # --------------------------------------------------------------
    # Build LangGraph
    # --------------------------------------------------------------

    graph = build_multi_agent_graph(
        orchestrator=orchestrator,
        rag_service=rag_service,
        data_agent=database_agent,
        critic_agent=critic,
        llm_client=gemini_client,
    )

    # --------------------------------------------------------------
    # Wrap graph in application service
    # --------------------------------------------------------------

    return AgenticRAGService(
        graph=graph,
    )