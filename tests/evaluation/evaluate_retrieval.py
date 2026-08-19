from app.database.database import SessionLocal
from app.dependencies.rag import get_retrieval_service
from app.evaluation.retrieval_dataset import CASES
from app.evaluation.runner import RetrievalEvaluationRunner
from app.models.users import User


# ============================================================
# CONFIGURATION
# ============================================================

EVALUATION_USER_ID = 9
TOP_K = 5


def main() -> None:

    db = SessionLocal()

    try:

        # -----------------------------------------------------
        # Load the real evaluation user
        # -----------------------------------------------------

        user = (
            db.query(User)
            .filter(
                User.user_id == EVALUATION_USER_ID
            )
            .first()
        )

        if user is None:
            raise RuntimeError(
                f"Evaluation user {EVALUATION_USER_ID} "
                "was not found."
            )

        print()
        print("=" * 70)
        print("INTELLEX RETRIEVAL EVALUATION")
        print("=" * 70)

        print(
            f"Evaluation user: "
            f"{user.name} "
            f"(user_id={user.user_id})"
        )

        print(
            f"Organization ID: "
            f"{user.organization_id}"
        )

        print(
            f"Department ID: "
            f"{user.department_id}"
        )

        print(
            f"Team ID: "
            f"{user.team_id}"
        )

        print(
            f"Evaluation cases: "
            f"{len(CASES)}"
        )

        print("=" * 70)
        print()

        # -----------------------------------------------------
        # Create evaluation runner
        # -----------------------------------------------------

        runner = RetrievalEvaluationRunner(
            retrieval_service=get_retrieval_service(),
            top_k=TOP_K,
        )

        # -----------------------------------------------------
        # Run evaluation
        # -----------------------------------------------------

        summary = runner.evaluate(
            db=db,
            current_user=user,
            cases=CASES,
        )

        # -----------------------------------------------------
        # Print summary
        # -----------------------------------------------------

        print()
        print("=" * 70)
        print("EVALUATION SUMMARY")
        print("=" * 70)

        print(
            f"Cases: "
            f"{summary.total_cases}"
        )

        print(
            f"Hit@{TOP_K}: "
            f"{summary.average_hit_at_k:.3f}"
        )

        print(
            f"Precision@{TOP_K}: "
            f"{summary.average_precision_at_k:.3f}"
        )

        print(
            f"Recall@{TOP_K}: "
            f"{summary.average_recall_at_k:.3f}"
        )

        print(
            f"MRR: "
            f"{summary.average_mrr:.3f}"
        )

        print("=" * 70)
        print()

        # -----------------------------------------------------
        # Print per-query results
        # -----------------------------------------------------

        for index, result in enumerate(
            summary.results,
            start=1,
        ):

            print(
                f"[{index}] "
                f"{result.query}"
            )

            print(
                "    Expected: "
                f"{CASES[index - 1].relevant_document_ids}"
            )

            print(
                "    Retrieved: "
                f"{result.retrieved_document_ids}"
            )

            print(
                f"    Hit@{TOP_K}: "
                f"{result.hit_at_k:.3f}"
            )

            print(
                f"    Precision@{TOP_K}: "
                f"{result.precision_at_k:.3f}"
            )

            print(
                f"    Recall@{TOP_K}: "
                f"{result.recall_at_k:.3f}"
            )

            print(
                f"    MRR: "
                f"{result.reciprocal_rank:.3f}"
            )

            print()

    finally:
        db.close()


if __name__ == "__main__":
    main()