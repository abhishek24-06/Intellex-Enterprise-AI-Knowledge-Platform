from unittest.mock import Mock

from app.dto.final_chunk import FinalChunk
from app.enums.chunk_type import ChunkType
from app.services.chunk_persistence.chunk_persistence_service import (
    ChunkPersistenceService,
)


def make_chunk(
    text: str,
    order_index: int,
    section_path: list[str] | None = None,
    metadata: dict | None = None,
) -> FinalChunk:

    return FinalChunk(
        text=text,
        elements=[],
        chunk_type=ChunkType.NARRATIVE,
        section_path=section_path or [],
        order_index=order_index,
        metadata=metadata or {},
    )


def make_service():

    embedding_service = Mock()

    service = ChunkPersistenceService(
        embedding_service=embedding_service
    )

    return service, embedding_service


def test_persist_empty_chunks():

    service, embedding_service = make_service()

    db = Mock()

    result = service.persist(
        db=db,
        chunks=[],
    )

    assert result == []

    embedding_service.embed_texts.assert_not_called()
    embedding_service.count_tokens.assert_not_called()

    db.add_all.assert_not_called()
    db.flush.assert_not_called()


def test_persist_chunks():

    service, embedding_service = make_service()

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
            order_index=5,
            section_path=["Introduction"],
            metadata={
                "document_id": 123,
                "page": 1,
            },
        ),
        make_chunk(
            text="Second chunk",
            order_index=10,
            section_path=[
                "Introduction",
                "Background",
            ],
            metadata={
                "document_id": 123,
                "page": 2,
            },
        ),
    ]

    result = service.persist(
        db=db,
        chunks=chunks,
    )

    assert len(result) == 2

    first = result[0]
    second = result[1]

    # First chunk
    assert first.document_id == 123
    assert first.chunk_index == 0
    assert first.chunk_text == "First chunk"
    assert first.token_count == 10
    assert len(first.embedding) == 1024

    # Second chunk
    assert second.document_id == 123
    assert second.chunk_index == 1
    assert second.chunk_text == "Second chunk"
    assert second.token_count == 20
    assert len(second.embedding) == 1024

    # Metadata preservation
    assert first.metadata_json["document_id"] == 123
    assert first.metadata_json["page"] == 1
    assert first.metadata_json["chunk_type"] == "narrative"
    assert first.metadata_json["section_path"] == [
        "Introduction"
    ]
    assert first.metadata_json["order_index"] == 5

    assert second.metadata_json["document_id"] == 123
    assert second.metadata_json["page"] == 2
    assert second.metadata_json["section_path"] == [
        "Introduction",
        "Background",
    ]
    assert second.metadata_json["order_index"] == 10

    # Batch embedding
    embedding_service.embed_texts.assert_called_once_with(
        [
            "First chunk",
            "Second chunk",
        ]
    )

    # Token counting
    assert embedding_service.count_tokens.call_count == 2

    # Database persistence
    db.add_all.assert_called_once()
    db.flush.assert_called_once()


def test_embedding_count_mismatch_is_rejected():

    service, embedding_service = make_service()

    embedding_service.embed_texts.return_value = [
        [0.1] * 1024,
    ]

    db = Mock()

    chunks = [
        make_chunk(
            text="First",
            order_index=0,
            metadata={"document_id": 123},
        ),
        make_chunk(
            text="Second",
            order_index=1,
            metadata={"document_id": 123},
        ),
    ]

    try:
        service.persist(
            db=db,
            chunks=chunks,
        )

        assert False, "Expected ValueError"

    except ValueError as exc:

        assert str(exc) == (
            "Embedding count does not match chunk count."
        )

    db.add_all.assert_not_called()
    db.flush.assert_not_called()    