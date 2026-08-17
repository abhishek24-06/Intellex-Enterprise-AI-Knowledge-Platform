from unittest.mock import Mock

import pytest

from app.dto.retrieved_chunk import RetrievedChunk
from app.services.generation.answer_generation_service import (
    AnswerGenerationService,
)


def make_chunk():

    return RetrievedChunk(
        document_id=24,
        chunk_id=100,
        chunk_index=0,
        chunk_text="Deepfake detection uses CNNs.",
        token_count=10,
        metadata={
            "document_id": 24,
        },
        vector_score=0.8,
        rerank_score=2.5,
    )


def make_service():

    llm_client = Mock()

    llm_client.generate.return_value = (
        "The system uses CNN-based deepfake detection."
    )

    prompt_builder = Mock()

    prompt_builder.build.return_value = (
        "SYSTEM PROMPT",
        "USER PROMPT",
    )

    service = AnswerGenerationService(
        llm_client=llm_client,
        prompt_builder=prompt_builder,
    )

    return (
        service,
        llm_client,
        prompt_builder,
    )


def test_empty_query_is_rejected():

    service, _, _ = make_service()

    with pytest.raises(
        ValueError,
        match="Query cannot be empty",
    ):
        service.generate(
            query="",
            chunks=[make_chunk()],
        )


def test_whitespace_query_is_rejected():

    service, _, _ = make_service()

    with pytest.raises(
        ValueError,
        match="Query cannot be empty",
    ):
        service.generate(
            query="   ",
            chunks=[make_chunk()],
        )


def test_empty_chunks_are_rejected():

    service, _, _ = make_service()

    with pytest.raises(
        ValueError,
        match="At least one retrieved chunk",
    ):
        service.generate(
            query="What is deepfake detection?",
            chunks=[],
        )


def test_prompt_builder_is_called():

    (
        service,
        _,
        prompt_builder,
    ) = make_service()

    chunks = [make_chunk()]

    service.generate(
        query="What is deepfake detection?",
        chunks=chunks,
    )

    prompt_builder.build.assert_called_once_with(
        query="What is deepfake detection?",
        chunks=chunks,
    )


def test_llm_receives_generated_prompts():

    (
        service,
        llm_client,
        _,
    ) = make_service()

    service.generate(
        query="What is deepfake detection?",
        chunks=[make_chunk()],
    )

    llm_client.generate.assert_called_once_with(
        system_prompt="SYSTEM PROMPT",
        user_prompt="USER PROMPT",
    )


def test_generated_answer_is_returned():

    (
        service,
        _,
        _,
    ) = make_service()

    result = service.generate(
        query="What is deepfake detection?",
        chunks=[make_chunk()],
    )

    assert result == (
        "The system uses CNN-based deepfake detection."
    )


def test_generated_answer_is_stripped():

    (
        service,
        llm_client,
        _,
    ) = make_service()

    llm_client.generate.return_value = (
        "   Grounded answer.   "
    )

    result = service.generate(
        query="What is deepfake detection?",
        chunks=[make_chunk()],
    )

    assert result == "Grounded answer."


def test_empty_llm_response_is_rejected():

    (
        service,
        llm_client,
        _,
    ) = make_service()

    llm_client.generate.return_value = ""

    with pytest.raises(
        RuntimeError,
        match="LLM returned an empty answer",
    ):
        service.generate(
            query="What is deepfake detection?",
            chunks=[make_chunk()],
        )