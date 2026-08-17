from unittest.mock import Mock

import pytest

from app.services.embedding.embedding_pipeline import (
    EmbeddingPipeline,
)


def make_chunk(
    text,
    document_id=18,
    chunk_type="narrative",
    section_path=None,
    order_index=0,
    metadata=None,
):
    chunk = Mock()

    chunk.text = text
    chunk.chunk_type = chunk_type
    chunk.section_path = section_path or []

    chunk.metadata = {
        "document_id": document_id,
        **(metadata or {}),
    }

    chunk.order_index = order_index

    return chunk


def make_pipeline():

    embedding_service = Mock()

    pipeline = EmbeddingPipeline(
        embedding_service=embedding_service
    )

    return pipeline, embedding_service


def test_empty_chunks():

    pipeline, embedding_service = make_pipeline()

    db = Mock()

    result = pipeline.process(
        db=db,
        chunks=[],
    )

    assert result == []

    embedding_service.embed_texts.assert_not_called()


def test_embeddings_are_generated_in_batch():

    pipeline, embedding_service = make_pipeline()

    embedding_service.embed_texts.return_value = [
        [0.1] * 1024,
        [0.2] * 1024,
    ]

    embedding_service.count_tokens.side_effect = [
        10,
        20,
    ]

    db = Mock()

    chunks = [
        make_chunk(
            text="First chunk",
            document_id=18,
            section_path=["Introduction"],
            order_index=10,
        ),
        make_chunk(
            text="Second chunk",
            document_id=18,
            section_path=[
                "Introduction",
                "Background",
            ],
            order_index=20,
        ),
    ]

    result = pipeline.process(
        db=db,
        chunks=chunks,
    )

    assert len(result) == 2

    # Critical assertion:
    # one batch call instead of one call per chunk.
    embedding_service.embed_texts.assert_called_once_with(
    texts=[
        "First chunk",
        "Second chunk",
    ]
)

    assert result[0].document_id == 18
    assert result[0].chunk_index == 0
    assert result[0].chunk_text == "First chunk"
    assert result[0].token_count == 10
    assert len(result[0].embedding) == 1024

    assert result[1].document_id == 18
    assert result[1].chunk_index == 1
    assert result[1].chunk_text == "Second chunk"
    assert result[1].token_count == 20
    assert len(result[1].embedding) == 1024

    assert (
        result[0].metadata_json["section_path"]
        == ["Introduction"]
    )

    assert (
        result[1].metadata_json["section_path"]
        == [
            "Introduction",
            "Background",
        ]
    )

    db.add_all.assert_called_once_with(result)
    db.flush.assert_called_once()


def test_embedding_count_mismatch_is_rejected():

    pipeline, embedding_service = make_pipeline()

    embedding_service.embed_texts.return_value = [
        [0.1] * 1024,
    ]

    db = Mock()

    chunks = [
        make_chunk("First"),
        make_chunk("Second"),
    ]

    with pytest.raises(
        ValueError,
        match="Embedding count does not match",
    ):
        pipeline.process(
            db=db,
            chunks=chunks,
        )

    db.add_all.assert_not_called()


def test_embedding_dimension_mismatch_is_rejected():

    pipeline, embedding_service = make_pipeline()

    embedding_service.embed_texts.return_value = [
        [0.1] * 768,
    ]

    db = Mock()

    chunks = [
        make_chunk("First"),
    ]

    with pytest.raises(
        ValueError,
        match="Invalid embedding dimension",
    ):
        pipeline.process(
            db=db,
            chunks=chunks,
        )

    db.add_all.assert_not_called()


def test_missing_document_id_is_rejected():

    pipeline, embedding_service = make_pipeline()

    embedding_service.embed_texts.return_value = [
        [0.1] * 1024,
    ]

    db = Mock()

    chunk = make_chunk("First")
    chunk.metadata = {}

    with pytest.raises(
        ValueError,
        match="Missing document_id",
    ):
        pipeline.process(
            db=db,
            chunks=[chunk],
        )

    db.add_all.assert_not_called()