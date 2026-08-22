from __future__ import annotations

import json
import sys
from pathlib import Path

from evaluation.hybrid_evaluator import (
    HybridEvaluator,
)
from evaluation.ragas_evaluator import (
    RagasEvaluator,
)
from app.services.generation.openrouter_client import (
    OpenRouterClient,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )


RUNTIME_RECORDS_PATH = (
    PROJECT_ROOT
    / "evaluation"
    / "evals"
    / "results"
    / "runtime_evaluation_records.json"
)

RESULTS_PATH = (
    PROJECT_ROOT
    / "evaluation"
    / "evals"
    / "results"
    / "evaluation_results.json"
)


def main():

    print(
        "Loading runtime evaluation records..."
    )

    ragas_evaluator = (
        RagasEvaluator()
    )

    records = (
        ragas_evaluator.load_runtime_records(
            RUNTIME_RECORDS_PATH
        )
    )

    knowledge_records = [
        record
        for record in records
        if record["category"]
        == "KNOWLEDGE"
        and record["retrieved_contexts"]
    ]

    hybrid_records = [
        record
        for record in records
        if record["category"]
        == "HYBRID"
    ]

    # --------------------------------------------------------------
    # RAGAS
    # --------------------------------------------------------------

    ragas_results = None

    if knowledge_records:

        print()
        print(
            "Running Ragas on KNOWLEDGE..."
        )

        dataset = (
            ragas_evaluator.build_runtime_dataset(
                knowledge_records
            )
        )

        ragas_results = (
            ragas_evaluator.evaluate(
                dataset
            )
        )

    # --------------------------------------------------------------
    # HYBRID
    # --------------------------------------------------------------

    hybrid_results = []

    hybrid_evaluator = HybridEvaluator(
        llm_client=OpenRouterClient()
    )

    for record in hybrid_records:

        print()
        print(
            "Evaluating HYBRID:",
            record["id"],
        )

        result = (
            hybrid_evaluator.evaluate(
                query=record["user_input"],
                database_evidence=(
                    record.get(
                        "database_evidence"
                    )
                ),
                retrieved_contexts=(
                    record.get(
                        "retrieved_contexts",
                        [],
                    )
                ),
                response=record["response"],
                reference=record["reference"],
            )
        )

        hybrid_results.append(
            {
                "id": record["id"],
                "database_correctness": (
                    result.database_correctness
                ),
                "document_grounding": (
                    result.document_grounding
                ),
                "combined_answer_correctness": (
                    result.combined_answer_correctness
                ),
                "reasoning": result.reasoning,
            }
        )

    # --------------------------------------------------------------
    # Save results
    # --------------------------------------------------------------

    output = {
        "ragas": (
            ragas_results.to_pandas()
            .to_dict(
                orient="records"
            )
            if ragas_results
            else []
        ),
        "hybrid": hybrid_results,
    }

    RESULTS_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with RESULTS_PATH.open(
        "w",
        encoding="utf-8",
    ) as file:

        json.dump(
            output,
            file,
            indent=2,
            default=str,
        )

    print()
    print(
        "=" * 80
    )
    print(
        "INTELLEX EVALUATION RESULTS"
    )
    print(
        "=" * 80
    )

    if ragas_results:
        print()
        print(
            "KNOWLEDGE / RAGAS:"
        )
        print(
            ragas_results
        )

    print()

    print(
        "HYBRID:"
    )

    for result in hybrid_results:

        print(
            f"\n{result['id']}"
        )

        print(
            "  Database correctness:",
            result[
                "database_correctness"
            ],
        )

        print(
            "  Document grounding:",
            result[
                "document_grounding"
            ],
        )

        print(
            "  Combined correctness:",
            result[
                "combined_answer_correctness"
            ],
        )

        print(
            "  Reasoning:",
            result["reasoning"],
        )

    print()
    print(
        "Saved:"
    )

    print(
        RESULTS_PATH
    )


if __name__ == "__main__":
    main()