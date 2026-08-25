from app.database.database import SessionLocal
from app.models.users import User

from app.agents.critic_agent import (
    CriticDecision,
    CriticResult,
    RetryTarget,
)

from app.agents.graph.graph import build_multi_agent_graph
from app.dependencies.agentic_rag import (
    get_orchestrator_agent,
    get_database_agent,
    get_rag_service,
)
from app.services.generation.provider_client import ProviderLLMClient


class AlwaysRetryCritic:

    def evaluate(
        self,
        *,
        query,
        answer,
        chunks=None,
        database_result=None,
    ):

        return CriticResult(
            decision=CriticDecision.RETRY,

            context_relevance=0.0,

            faithfulness=0.0,

            answer_correctness=0.0,

            reason=(
                "Forced RETRY for end-to-end "
                "retry-limit testing."
            ),

            retry_target=RetryTarget.KNOWLEDGE,

            improved_query=(
                "Retrieve the relevant enterprise "
                "information again."
            ),
        )


def main():

    db = SessionLocal()

    try:

        current_user = (
            db.query(User)
            .filter(
                User.user_id == 9
            )
            .first()
        )

        if current_user is None:
            raise RuntimeError(
                "User id=9 not found."
            )

        print(
            "Authenticated user:"
        )

        print(
            "  id =",
            current_user.user_id,
        )

        print(
            "  email =",
            current_user.email,
        )

        print(
            "\nBuilding test graph..."
        )

        graph = build_multi_agent_graph(
            orchestrator=(
                get_orchestrator_agent()
            ),

            rag_service=(
                get_rag_service()
            ),

            data_agent=(
                get_database_agent()
            ),

            # IMPORTANT:
            # Replace the real critic with
            # our test critic.
            critic_agent=(
                AlwaysRetryCritic()
            ),

            llm_client=(
                ProviderLLMClient()
            ),
        )

        print(
            "Test graph created."
        )

        print(
            "\nRunning forced-retry test..."
        )

        result = graph.invoke(
            {
                "original_query": (
                    "What operational checks should my department "
    "perform before making a service change?"
                ),

                "attempt": 0,



                "max_retries": 2,

                "history": [],
            },

            context={
                "db": db,
                "current_user": current_user,
            },
        )

        print(
            "\n========== TEST RESULT =========="
        )

        print(
            "attempt =",
            result.get("attempt"),
            
        )
        print(
            "retry_count =",
            result.get("retry_count"),
)        

        print(
            "max_retries =",
            result.get("max_retries"),
        )

        print(
            "final_answer =",
            result.get("final_answer"),
        )

        print(
            "\nHISTORY:"
        )

        for item in result.get(
            "history",
            [],
        ):
            print(item)

        print(
            "================================="
        )

    finally:

        db.close()


if __name__ == "__main__":
    main()