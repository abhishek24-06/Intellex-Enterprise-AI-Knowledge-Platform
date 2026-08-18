from unittest.mock import Mock

import pytest

from app.services.query_contextualizer import (
    QueryContextualizer,
)


def make_service():
    llm = Mock()
    llm.generate.return_value = (
        "How do I apply for annual leave?"
    )

    return QueryContextualizer(
        llm_client=llm,
    ), llm


def test_empty_query_is_rejected():

    service, _ = make_service()

    with pytest.raises(
        ValueError,
        match="Query cannot be empty",
    ):
        service.contextualize(
            query="",
            history=[],
        )


def test_no_history_returns_original_query():

    service, llm = make_service()

    result = service.contextualize(
        query="What is annual leave?",
        history=[],
    )

    assert result == "What is annual leave?"

    llm.generate.assert_not_called()


def test_history_is_used_for_contextualization():

    service, llm = make_service()

    history = [
        (
            "What is the annual leave policy?",
            "Employees receive 20 days of annual leave.",
        )
    ]

    result = service.contextualize(
        query="How do I apply for it?",
        history=history,
    )

    assert result == (
        "How do I apply for annual leave?"
    )

    llm.generate.assert_called_once()


def test_contextualized_query_is_trimmed():

    service, llm = make_service()

    llm.generate.return_value = (
        "   How do I apply for annual leave?   "
    )

    result = service.contextualize(
        query="How do I apply for it?",
        history=[
            (
                "What is annual leave?",
                "20 days.",
            )
        ],
    )

    assert result == (
        "How do I apply for annual leave?"
    )


def test_empty_llm_response_is_rejected():

    service, llm = make_service()

    llm.generate.return_value = ""

    with pytest.raises(
        RuntimeError,
        match="empty query",
    ):
        service.contextualize(
            query="How do I apply for it?",
            history=[
                (
                    "What is annual leave?",
                    "20 days.",
                )
            ],
        )