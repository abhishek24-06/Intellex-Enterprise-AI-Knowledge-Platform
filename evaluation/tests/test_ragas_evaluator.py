from evaluation.ragas_evaluator import (
    RagasEvaluator,
)


def test_ragas_evaluator_builds_runtime_dataset():

    evaluator = object.__new__(
        RagasEvaluator
    )

    dataset = evaluator.build_runtime_dataset(
        [
            {
                "user_input": "What is Intellex?",
                "retrieved_contexts": [
                    "Intellex is an enterprise knowledge platform."
                ],
                "response": (
                    "Intellex is an enterprise "
                    "knowledge platform."
                ),
                "reference": (
                    "Intellex is an enterprise "
                    "knowledge platform."
                ),
            }
        ]
    )

    assert len(dataset.samples) == 1

    features = dataset.features()

    assert "user_input" in features

    assert "retrieved_contexts" in features

    assert "response" in features

    assert "reference" in features