import pytest
from sqlalchemy import select

from app.database.database import SessionLocal
from app.dto.final_chunk import FinalChunk
from app.enums.chunk_type import ChunkType
from app.models.document_chunks import DocumentChunk
from app.models.documents import Document
from app.services.chunk_persistence.chunk_persistence_service import (
    ChunkPersistenceService,
)
from app.services.embedding.bge_m3_embedding_service import (
    BGEM3EmbeddingService,
)


pytestmark = pytest.mark.integration


@pytest.fixture(scope="session")
def embedding_service():
    """
    Load BGE-M3 only once for the entire integration test session.
    """
    return BGEM3EmbeddingService()


@pytest.fixture
def db():
    """
    Use one real database transaction for the test.

    Nothing is committed, so the temporary document and
    its chunks are rolled back automatically.
    """
    session = SessionLocal()

    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture
def temporary_document(db):
    """
    Create a temporary Document using valid organization/user
    relationships from an existing document.

    The transaction is rolled back after the test.
    """

    source_document = db.execute(
        select(Document)
        .order_by(Document.document_id)
        .limit(1)
    ).scalar_one_or_none()

    if source_document is None:
        pytest.skip(
            "No existing document available to create "
            "integration-test fixture."
        )

    document = Document(
        organization_id=source_document.organization_id,
        uploaded_by=source_document.uploaded_by,
        document_type=source_document.document_type,
        visibility=source_document.visibility,
        title="__INT_TEST_CHUNK_PERSISTENCE__",
        description="Temporary integration test document",
        original_filename="integration_test.txt",
        stored_filename="integration_test.txt",
        status=source_document.status,
        file_path="integration-test/integration_test.txt",
        file_size=100,
        mime_type="text/plain",
        embedding_model=None,
        processing_error=None,
        is_deleted=False,
        version=1,
    )

    db.add(document)
    db.flush()

    return document


def make_chunk(
    text: str,
    order_index: int,
    document_id: int,
    section_path: list[str],
    page: int,
) -> FinalChunk:

    return FinalChunk(
        text=text,
        elements=[],
        chunk_type=ChunkType.NARRATIVE,
        section_path=section_path,
        order_index=order_index,
        metadata={
            "document_id": document_id,
            "page": page,
            "source": "integration_test",
        },
    )


def test_real_bge_m3_chunk_persistence(
    db,
    temporary_document,
    embedding_service,
):
    """
    End-to-end 6C verification:

        FinalChunk[]
            ↓
        real BGE-M3
            ↓
        ChunkPersistenceService
            ↓
        real SQLAlchemy
            ↓
        Supabase PostgreSQL
            ↓
        DocumentChunk
            ↓
        pgvector VECTOR(1024)
    """

    document_id = temporary_document.document_id

    chunks = [
        make_chunk(
            text=(
                "Intellex is an enterprise knowledge "
                "intelligence platform."
            ),
            order_index=10,
            document_id=document_id,
            section_path=["Introduction"],
            page=1,
        ),
        make_chunk(
            text=(
                "Documents are retrieved using "
                "vector similarity search."
            ),
            order_index=20,
            document_id=document_id,
            section_path=[
                "Introduction",
                "Retrieval",
            ],
            page=2,
        ),
        make_chunk(
            text=(
                "Employee information is stored "
                "in PostgreSQL."
            ),
            order_index=30,
            document_id=document_id,
            section_path=[
                "Employee Data",
            ],
            page=3,
        ),
    ]

    service = ChunkPersistenceService(
        embedding_service=embedding_service
    )

    # ---------------------------------------------------------
    # Persist using REAL BGE-M3 + REAL PostgreSQL
    # ---------------------------------------------------------

    persisted_chunks = service.persist(
        db=db,
        chunks=chunks,
    )

    # ---------------------------------------------------------
    # Basic persistence checks
    # ---------------------------------------------------------

    assert len(persisted_chunks) == len(chunks)

    for index, chunk in enumerate(persisted_chunks):

        assert chunk.document_id == document_id
        assert chunk.chunk_index == index

        assert chunk.chunk_text == chunks[index].text

        assert chunk.token_count > 0

        assert chunk.embedding is not None
        assert len(chunk.embedding) == 1024

    # ---------------------------------------------------------
    # Verify chunk indexes
    # ---------------------------------------------------------

    indexes = [
        chunk.chunk_index
        for chunk in persisted_chunks
    ]

    assert indexes == [0, 1, 2]

    # ---------------------------------------------------------
    # Verify metadata
    # ---------------------------------------------------------

    first = persisted_chunks[0]
    second = persisted_chunks[1]
    third = persisted_chunks[2]

    assert first.metadata_json["document_id"] == document_id
    assert first.metadata_json["page"] == 1
    assert first.metadata_json["source"] == "integration_test"
    assert first.metadata_json["section_path"] == [
        "Introduction"
    ]

    assert second.metadata_json["section_path"] == [
        "Introduction",
        "Retrieval",
    ]

    assert third.metadata_json["section_path"] == [
        "Employee Data"
    ]

    # ---------------------------------------------------------
    # Verify actual rows can be queried back
    # ---------------------------------------------------------

    stored_chunks = db.execute(
        select(DocumentChunk)
        .where(
            DocumentChunk.document_id == document_id
        )
        .order_by(DocumentChunk.chunk_index)
    ).scalars().all()

    assert len(stored_chunks) == 3

    # ---------------------------------------------------------
    # Verify database values
    # ---------------------------------------------------------

    for index, stored in enumerate(stored_chunks):

        assert stored.document_id == document_id
        assert stored.chunk_index == index

        assert stored.chunk_text == chunks[index].text

        assert stored.token_count > 0

        assert stored.embedding is not None
        assert len(stored.embedding) == 1024

    # ---------------------------------------------------------
    # Verify vectors are actually different
    # ---------------------------------------------------------

    assert (
        stored_chunks[0].embedding
        != stored_chunks[1].embedding
    )

    assert (
        stored_chunks[1].embedding
        != stored_chunks[2].embedding
    )

    # ---------------------------------------------------------
    # Verify metadata survives database round-trip
    # ---------------------------------------------------------

    assert (
        stored_chunks[0]
        .metadata_json["section_path"]
        == ["Introduction"]
    )

    assert (
        stored_chunks[1]
        .metadata_json["section_path"]
        == [
            "Introduction",
            "Retrieval",
        ]
    )

    assert (
        stored_chunks[2]
        .metadata_json["section_path"]
        == ["Employee Data"]
    )