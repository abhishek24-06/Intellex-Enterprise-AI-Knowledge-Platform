import pytest
from sqlalchemy import select

from app.database.database import SessionLocal
from app.models.document_chunks import DocumentChunk
from app.services.embedding.bge_m3_embedding_service import (
    BGEM3EmbeddingService,
)
from app.services.embedding.document_embedding_ingestion_service import (
    DocumentEmbeddingIngestionService,
)

from tests.embedding.test_embedding_pipeline_integration import (
    DEBUG_CHUNKS_FILE,
    load_final_chunks,
)


# ======================================================================
# FIXTURES
# ======================================================================


@pytest.fixture(scope="session")
def embedding_service():
    """
    Load BGE-M3 only once for the test session.
    """

    return BGEM3EmbeddingService()


@pytest.fixture
def db():
    session = SessionLocal()

    try:
        yield session

    finally:
        session.rollback()
        session.close()


# ======================================================================
# REAL INGESTION TEST
# ======================================================================


def test_real_document_embedding_ingestion(
    db,
    embedding_service,
):
    """
    Real ingestion test.

    Unlike the previous integration test,
    this test COMMITS the chunks.

    FinalChunk[]
        ↓
    DocumentEmbeddingIngestionService
        ↓
    BGE-M3
        ↓
    DocumentChunk
        ↓
    PostgreSQL / pgvector
        ↓
    COMMIT
    """

    # --------------------------------------------------------------
    # 1. Load actual FinalChunk output
    # --------------------------------------------------------------

    chunks = load_final_chunks(
        DEBUG_CHUNKS_FILE
    )

    assert len(chunks) == 10

    document_id = (
        chunks[0]
        .metadata["document_id"]
    )

    # --------------------------------------------------------------
    # 2. Create ingestion service
    # --------------------------------------------------------------

    service = (
        DocumentEmbeddingIngestionService(
            embedding_service=embedding_service
        )
    )

    # --------------------------------------------------------------
    # 3. Perform REAL ingestion
    # --------------------------------------------------------------

    persisted_chunks = service.ingest(
        db=db,
        chunks=chunks,
    )

    # --------------------------------------------------------------
    # 4. Verify result
    # --------------------------------------------------------------

    assert len(
        persisted_chunks
    ) == 10

    # --------------------------------------------------------------
    # 5. Query database AFTER COMMIT
    # --------------------------------------------------------------

    stored_chunks = (
        db.execute(
            select(DocumentChunk)
            .where(
                DocumentChunk.document_id
                == document_id
            )
            .order_by(
                DocumentChunk.chunk_index
            )
        )
        .scalars()
        .all()
    )

    # --------------------------------------------------------------
    # 6. Verify database rows
    # --------------------------------------------------------------

    assert len(
        stored_chunks
    ) == 10

    # --------------------------------------------------------------
    # 7. Verify embeddings
    # --------------------------------------------------------------

    for index, chunk in enumerate(
        stored_chunks
    ):

        assert (
            chunk.document_id
            == document_id
        )

        assert (
            chunk.chunk_index
            == index
        )

        assert chunk.embedding is not None

        assert (
            len(chunk.embedding)
            == 1024
        )

        assert (
            chunk.token_count
            > 0
        )

    # --------------------------------------------------------------
    # 8. Verify metadata
    # --------------------------------------------------------------

    for index, chunk in enumerate(
        stored_chunks
    ):

        original = chunks[index]

        assert (
            chunk.metadata_json[
                "document_id"
            ]
            == document_id
        )

        assert (
            chunk.metadata_json[
                "section_path"
            ]
            == original.section_path
        )

        assert (
            chunk.metadata_json[
                "order_index"
            ]
            == original.order_index
        )

        assert (
            chunk.metadata_json[
                "chunk_type"
            ]
            == original.chunk_type.value
        )

    # --------------------------------------------------------------
    # 9. Verify text
    # --------------------------------------------------------------

    for index, chunk in enumerate(
        stored_chunks
    ):

        assert (
            chunk.chunk_text
            == chunks[index].text
        )

    print()
    print("=" * 70)
    print("REAL DOCUMENT INGESTION SUCCESS")
    print("=" * 70)
    print(
        f"Document ID       : {document_id}"
    )
    print(
        f"Chunks persisted  : {len(stored_chunks)}"
    )
    print(
        "Embedding dimension: 1024"
    )
    print(
        "Database           : Supabase PostgreSQL"
    )
    print(
        "Vector store       : pgvector"
    )
    print("=" * 70)