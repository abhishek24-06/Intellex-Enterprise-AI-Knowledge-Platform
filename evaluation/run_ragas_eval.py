from __future__ import annotations

import json
from pathlib import Path

from app.dependencies.agentic_rag import (
    get_agentic_rag_service,
)

from app.database.database import (
    SessionLocal,
)

from app.models.users import User

from evaluation.ragas_evaluator import (
    RagasEvaluator,
)


DATASET_PATH = (
    Path(__file__).parent
    / "datasets"
    / "rag_eval_dataset.json"
)

OUTPUT_PATH = (
    Path(__file__).parent
    / "results"
    / "ragas_results.json"
)


def get_test_user(db):
    user = (
        db.query(User)
        .filter(
            User.is_active.is_(True),
            User.organization_id.is_not(None),
        )
        .order_by(
            User.user_id.asc()
        )
        .first()
    )

    if user is None:
        raise RuntimeError(
            "No suitable evaluation user found."
        )

    return user


def main():

    evaluator = RagasEvaluator()

    cases = (
        evaluator.load_dataset(
            DATASET_PATH
        )
    )

    db = SessionLocal()

    try:

        user = get_test_user(db)

        agentic_rag_service = (
            get_agentic_rag_service()
        )

        evaluation_records = []

        for case in cases:

            print(
                f"\nRunning: {case['id']}"
            )

            result = agentic_rag_service.answer(
                db=db,
                query=case["user_input"],
                current_user=user,
            )

            retrieved_contexts = [
                chunk.chunk_text
                for chunk in result.sources
            ]

            evaluation_records.append(
                {
                    "id": case["id"],
                    "category": case["category"],
                    "user_input": case["user_input"],
                    "retrieved_contexts": (
                        retrieved_contexts
                    ),
                    "response": result.answer,
                    "reference": case["reference"],
                }
            )

            print(
                "Route:",
                "retrieval sources="
                + str(len(result.sources)),
            )

        ragas_dataset = (
            evaluator.build_runtime_dataset(
                evaluation_records
            )
        )

        results = evaluator.evaluate(
            ragas_dataset
        )

        OUTPUT_PATH.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        with OUTPUT_PATH.open(
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                {
                    "metrics": (
                        results.to_pandas()
                        .to_dict(
                            orient="records"
                        )
                    )
                },
                file,
                indent=2,
                default=str,
            )

        print("\n=== RAGAS RESULTS ===")
        print(results)

    finally:
        db.close()


if __name__ == "__main__":
    main()