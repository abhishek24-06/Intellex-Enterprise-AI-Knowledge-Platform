from app.agents.graph.multi_agent_routing import (
    route_after_multi_agent_critic,
)
from app.agents.critic_agent import (
    CriticDecision,
    CriticResult,
    RetryTarget,
)


def make_retry_critique():

    return CriticResult(
        decision=CriticDecision.RETRY,

        context_relevance=0.0,

        faithfulness=0.0,

        answer_correctness=0.0,

        reason="Forced retry for testing.",

        retry_target=RetryTarget.KNOWLEDGE,

        improved_query="Retry knowledge retrieval.",
    )


def main():

    critique = make_retry_critique()

    print(
        "\n========== RETRY LIMIT TEST ==========\n"
    )

    for retry_count in range(4):

        state = {
            "critique": critique,
            "retry_count": retry_count,
            "max_retries": 2,
        }

        route = route_after_multi_agent_critic(
            state
        )

        print(
            f"retry_count={retry_count} "
            f"-> route={route}"
        )

    print(
        "\n======================================\n"
    )


if __name__ == "__main__":
    main()