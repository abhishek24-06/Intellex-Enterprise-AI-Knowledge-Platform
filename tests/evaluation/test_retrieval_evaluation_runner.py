from types import SimpleNamespace
from unittest.mock import Mock,ANY

import pytest

from app.evaluation.models import EvaluationCase
from app.evaluation.runner import (
    RetrievalEvaluationRunner,
)


def make_chunk(document_id: int):

    return SimpleNamespace(
        document_id=document_id,
    )


def make_case(
    *,
    relevant_document_ids: set[int],
):

    return EvaluationCase(
        query="test query",
        relevant_document_ids=(
            relevant_document_ids
        ),
    )


def test_unique_document_ids_preserve_order():

    runner = RetrievalEvaluationRunner(
        retrieval_service=Mock(),
    )

    chunks = [
        make_chunk(24),
        make_chunk(24),
        make_chunk(28),
        make_chunk(35),
        make_chunk(28),
    ]

    result = runner._unique_document_ids(
        chunks
    )

    assert result == [
        24,
        28,
        35,
    ]


def test_empty_dataset_is_rejected():

    runner = RetrievalEvaluationRunner(
        retrieval_service=Mock(),
    )

    with pytest.raises(
        ValueError,
        match="Evaluation dataset cannot be empty",
    ):
        runner.evaluate(
            db=Mock(),
            current_user=Mock(),
            cases=[],
        )


def test_invalid_top_k_is_rejected():

    with pytest.raises(
        ValueError,
        match="top_k must be greater than zero",
    ):
        RetrievalEvaluationRunner(
            retrieval_service=Mock(),
            top_k=0,
        )


def test_evaluate_case_calculates_metrics():

    retrieval_service = Mock()

    retrieval_service.retrieve.return_value = [
        make_chunk(24),
        make_chunk(24),
        make_chunk(28),
        make_chunk(35),
    ]

    runner = RetrievalEvaluationRunner(
        retrieval_service=retrieval_service,
        top_k=3,
    )

    case = make_case(
        relevant_document_ids={28},
    )

    result = runner.evaluate_case(
        db=Mock(),
        current_user=Mock(),
        case=case,
    )

    assert result.query == "test query"

    assert result.retrieved_document_ids == [
        24,
        28,
        35,
    ]

    assert result.hit_at_k == 1.0
    assert result.precision_at_k == pytest.approx(
        1 / 3
    )
    assert result.recall_at_k == 1.0
    assert result.reciprocal_rank == 0.5


def test_evaluate_case_passes_correct_limits():

    retrieval_service = Mock()

    retrieval_service.retrieve.return_value = [
        make_chunk(24),
    ]

    runner = RetrievalEvaluationRunner(
        retrieval_service=retrieval_service,
        top_k=5,
    )

    case = make_case(
        relevant_document_ids={24},
    )

    runner.evaluate_case(
        db=Mock(),
        current_user=Mock(),
        case=case,
    )

    retrieval_service.retrieve.assert_called_once_with(
        db=ANY,
        query="test query",
        current_user=ANY,
        vector_top_k=30,
        rerank_top_k=5,
    )


def test_evaluate_returns_summary():

    retrieval_service = Mock()

    retrieval_service.retrieve.side_effect = [
        [
            make_chunk(24),
        ],
        [
            make_chunk(99),
        ],
    ]

    runner = RetrievalEvaluationRunner(
        retrieval_service=retrieval_service,
        top_k=5,
    )

    cases = [
        make_case(
            relevant_document_ids={24},
        ),
        make_case(
            relevant_document_ids={35},
        ),
    ]

    summary = runner.evaluate(
        db=Mock(),
        current_user=Mock(),
        cases=cases,
    )

    assert summary.total_cases == 2

    assert summary.average_hit_at_k == 0.5

    assert summary.average_precision_at_k == 0.5

    assert summary.average_recall_at_k == 0.5

    assert summary.average_mrr == 0.5

    assert len(summary.results) == 2