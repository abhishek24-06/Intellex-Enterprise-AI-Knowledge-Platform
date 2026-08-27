from __future__ import annotations

from langgraph.graph import (
    END,
    START,
    StateGraph,
)

from app.agents.graph.execution_timing import (
    timed_node,
)

from app.agents.graph.multi_agent_nodes import (
    conversational_node,
    database_agent_node,
    multi_agent_critic_node,
    multi_agent_finalize_node,
    multi_agent_knowledge_node,
    multi_agent_prepare_retry_node,
    orchestrator_node,
    synthesis_node,
)

from app.agents.graph.multi_agent_routing import (
    route_after_multi_agent_critic,
    route_after_orchestrator,
    route_after_retry_target,
    route_after_synthesis,
    route_after_agent,
)

from app.agents.multi_agent_state import (
    MultiAgentContext,
    MultiAgentState,
)


def build_multi_agent_graph(
    *,
    orchestrator,
    rag_service,
    data_agent,
    critic_agent,
    llm_client,
):

    builder = StateGraph(
        MultiAgentState,
        context_schema=MultiAgentContext,
    )
    # ORCHESTRATOR
    def timed_orchestrator_node(
        state,
    ):
        return orchestrator_node(
            state,
            orchestrator=orchestrator,
        )

    builder.add_node(
        "orchestrator",
        timed_node(
            agent_name="orchestrator",
            node=timed_orchestrator_node,
            with_runtime=False,
        ),
    )
    # KNOWLEDGE
    def timed_knowledge_node(
        state,
        runtime,
    ):
        return multi_agent_knowledge_node(
            state,
            runtime,
            rag_service=rag_service,
        )

    builder.add_node(
        "knowledge_agent",
        timed_node(
            agent_name="knowledge_agent",
            node=timed_knowledge_node,
            with_runtime=True,
        ),
    )
    # DATABASE
    def timed_database_node(
        state,
        runtime,
    ):
        return database_agent_node(
            state,
            runtime,
            data_agent=data_agent,
        )

    builder.add_node(
        "database_agent",
        timed_node(
            agent_name="database_agent",
            node=timed_database_node,
            with_runtime=True,
        ),
    )

    def timed_conversational_node(state):
        return conversational_node(
            state,
            llm_client=llm_client,
        )


    builder.add_node(
        "conversational_agent",
        timed_node(
            agent_name="conversational_agent",
            node=timed_conversational_node,
            with_runtime=False,
        ),
    )

    # SYNTHESIS
    def timed_synthesis_node(
        state,
    ):
        return synthesis_node(
            state,
            llm_client=llm_client,
        )

    builder.add_node(
        "synthesis",
        timed_node(
            agent_name="synthesis",
            node=timed_synthesis_node,
            with_runtime=False,
        ),
    )
    # CRITIC
    def timed_critic_node(
        state,
    ):
        return multi_agent_critic_node(
            state,
            critic_agent=critic_agent,
        )

    builder.add_node(
        "multi_agent_critic",
        timed_node(
            agent_name="multi_agent_critic",
            node=timed_critic_node,
            with_runtime=False,
        ),
    )
    # RETRY PREPARATION
    builder.add_node(
        "multi_agent_prepare_retry",
        timed_node(
            agent_name="multi_agent_prepare_retry",
            node=multi_agent_prepare_retry_node,
            with_runtime=False,
        ),
    )
    # FINALIZE
    builder.add_node(
        "multi_agent_finalize",
        timed_node(
            agent_name="finalize",
            node=multi_agent_finalize_node,
            with_runtime=False,
        ),
    )
    # EDGES
    builder.add_edge(
        START,
        "orchestrator",
    )

    builder.add_conditional_edges(
        "orchestrator",
        route_after_orchestrator,
        {
            "knowledge": "knowledge_agent",
            "database": "database_agent",
            "conversational": "conversational_agent",
        },
    )

    builder.add_conditional_edges(
        "knowledge_agent",
        route_after_agent,
        {
            "synthesis": "synthesis",
            "finalize": "multi_agent_finalize",
        },
    )

    builder.add_conditional_edges(
        "database_agent",
        route_after_agent,
        {
            "synthesis": "synthesis",
            "finalize": "multi_agent_finalize",
        },
    )

    builder.add_edge(
    "conversational_agent",
    END,
)

    builder.add_conditional_edges(
        "synthesis",
        route_after_synthesis,
        {
            "finalize": "multi_agent_finalize",
            "critic": "multi_agent_critic",
        },
    )

    builder.add_conditional_edges(
        "multi_agent_critic",
        route_after_multi_agent_critic,
        {
            "retry": "multi_agent_prepare_retry",
            "finalize": "multi_agent_finalize",
        },
    )

    builder.add_conditional_edges(
        "multi_agent_prepare_retry",
        route_after_retry_target,
        {
            "knowledge": "knowledge_agent",
            "database": "database_agent",
        },
    )

    builder.add_edge(
        "multi_agent_finalize",
        END,
    )

    return builder.compile()