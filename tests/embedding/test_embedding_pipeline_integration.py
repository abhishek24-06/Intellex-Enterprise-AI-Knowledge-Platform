import ast
import re
from pathlib import Path

import pytest
from sqlalchemy import select

from app.database.database import SessionLocal
from app.dto.final_chunk import FinalChunk
from app.enums.chunk_type import ChunkType
from app.models.document_chunks import DocumentChunk
from app.models.documents import Document
from app.services.embedding.bge_m3_embedding_service import (
    BGEM3EmbeddingService,
)
from app.services.embedding.embedding_pipeline import (
    EmbeddingPipeline,
)


# ======================================================================
# PATHS
# ======================================================================

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DEBUG_CHUNKS_FILE = (
    PROJECT_ROOT / "debug_txt_chunks.txt"
)


# ======================================================================
# FIXTURES
# ======================================================================


@pytest.fixture(scope="session")
def embedding_service():
    """
    Load BGE-M3 once for the entire pytest session.

    The expensive model initialization therefore happens only once.
    """

    return BGEM3EmbeddingService()


@pytest.fixture
def db():
    """
    Real PostgreSQL/Supabase database session.

    The test transaction is rolled back after the test.
    """

    session = SessionLocal()

    try:
        yield session

    finally:
        session.rollback()
        session.close()


# ======================================================================
# FINAL CHUNK PARSER
# ======================================================================


def load_final_chunks(
    path: Path,
) -> list[FinalChunk]:
    """
    Parse the actual debug FinalChunk output.

    Expected structure:

        Document ID : 17
        Total chunks: 10

        CHUNK 0
        chunk_type   : ChunkType.NARRATIVE
        order_index  : 0
        section_path : []

        TEXT:
        ...

        METADATA:
        {...}
    """

    # ------------------------------------------------------------------
    # 1. Check file
    # ------------------------------------------------------------------

    if not path.exists():
        raise FileNotFoundError(
            f"Final chunk output not found: {path}"
        )

    # ------------------------------------------------------------------
    # 2. Read file
    # ------------------------------------------------------------------

    content = path.read_text(
        encoding="utf-8"
    )

    # Normalize Windows line endings.
    content = content.replace(
        "\r\n",
        "\n",
    )

    # ------------------------------------------------------------------
    # 3. Extract Document ID
    # ------------------------------------------------------------------

    document_match = re.search(
        r"Document ID\s*:\s*(\d+)",
        content,
    )

    if not document_match:
        raise ValueError(
            "Could not find Document ID "
            "in final chunk output."
        )

    document_id = int(
        document_match.group(1)
    )

    # ------------------------------------------------------------------
    # 4. Extract total chunk count
    # ------------------------------------------------------------------

    total_match = re.search(
        r"Total chunks\s*:\s*(\d+)",
        content,
    )

    if not total_match:
        raise ValueError(
            "Could not find total chunk count."
        )

    expected_count = int(
        total_match.group(1)
    )

    # ------------------------------------------------------------------
    # 5. Find CHUNK headers
    #
    # We intentionally do NOT depend on the exact number of "-"
    # characters in the separator.
    # ------------------------------------------------------------------

    chunk_header_pattern = re.compile(
        r"^CHUNK\s+(?P<chunk_index>\d+)\s*$",
        re.MULTILINE,
    )

    headers = list(
        chunk_header_pattern.finditer(
            content
        )
    )

    if len(headers) != expected_count:
        raise ValueError(
            "Chunk header count does not match "
            f"reported count. "
            f"Expected={expected_count}, "
            f"Found={len(headers)}"
        )

    chunks: list[FinalChunk] = []

    # ==================================================================
    # Parse each CHUNK block
    # ==================================================================

    for position, header in enumerate(
        headers
    ):

        chunk_index = int(
            header.group("chunk_index")
        )

        # --------------------------------------------------------------
        # Determine where this chunk block ends
        # --------------------------------------------------------------

        block_start = header.end()

        if position + 1 < len(headers):

            block_end = headers[
                position + 1
            ].start()

        else:

            # Last chunk ends at end of file.
            block_end = len(content)

        block = content[
            block_start:block_end
        ]

        # --------------------------------------------------------------
        # Remove separator lines surrounding the block
        # --------------------------------------------------------------

        block = block.strip()

        block = re.sub(
            r"^-+\s*\n",
            "",
            block,
            count=1,
        )

        block = re.sub(
            r"\n-+\s*$",
            "",
            block,
            count=1,
        )

        block = block.strip()

        # ==============================================================
        # chunk_type
        # ==============================================================

        chunk_type_match = re.search(
            r"^chunk_type\s*:\s*(.+)$",
            block,
            re.MULTILINE,
        )

        if not chunk_type_match:
            raise ValueError(
                f"Could not find chunk_type "
                f"for CHUNK {chunk_index}."
            )

        chunk_type_raw = (
            chunk_type_match.group(1)
            .strip()
        )

        # --------------------------------------------------------------
        # Convert:
        #
        # ChunkType.NARRATIVE
        #
        # into:
        #
        # ChunkType.NARRATIVE enum
        # --------------------------------------------------------------

        if chunk_type_raw.startswith(
            "ChunkType."
        ):

            enum_name = (
                chunk_type_raw
                .split(
                    ".",
                    1,
                )[1]
            )

            try:

                chunk_type = ChunkType[
                    enum_name
                ]

            except KeyError as exc:

                raise ValueError(
                    f"Unknown ChunkType: "
                    f"{chunk_type_raw}"
                ) from exc

        else:

            try:

                chunk_type = ChunkType(
                    chunk_type_raw
                )

            except ValueError as exc:

                raise ValueError(
                    f"Unknown ChunkType: "
                    f"{chunk_type_raw}"
                ) from exc

        # ==============================================================
        # order_index
        # ==============================================================

        order_match = re.search(
            r"^order_index\s*:\s*(\d+)$",
            block,
            re.MULTILINE,
        )

        if not order_match:
            raise ValueError(
                f"Could not find order_index "
                f"for CHUNK {chunk_index}."
            )

        order_index = int(
            order_match.group(1)
        )

        # ==============================================================
        # section_path
        # ==============================================================

        section_match = re.search(
            r"^section_path\s*:\s*(.*)$",
            block,
            re.MULTILINE,
        )

        if not section_match:
            raise ValueError(
                f"Could not find section_path "
                f"for CHUNK {chunk_index}."
            )

        section_path_raw = (
            section_match.group(1)
            .strip()
        )

        if section_path_raw:

            try:

                section_path = ast.literal_eval(
                    section_path_raw
                )

            except (
                ValueError,
                SyntaxError,
            ) as exc:

                raise ValueError(
                    f"Could not parse section_path "
                    f"for CHUNK {chunk_index}: "
                    f"{section_path_raw}"
                ) from exc

        else:

            section_path = []

        if not isinstance(
            section_path,
            list,
        ):
            raise ValueError(
                f"section_path for CHUNK "
                f"{chunk_index} must be a list."
            )

        # ==============================================================
        # TEXT
        # ==============================================================

        text_match = re.search(
            r"TEXT:\s*\n(?P<text>.*?)(?=\nMETADATA:)",
            block,
            re.DOTALL,
        )

        if not text_match:
            raise ValueError(
                f"Could not find TEXT "
                f"for CHUNK {chunk_index}."
            )

        text = (
            text_match.group("text")
            .strip()
        )

        if not text:
            raise ValueError(
                f"CHUNK {chunk_index} "
                "contains empty text."
            )

        # ==============================================================
        # METADATA
        # ==============================================================

        metadata_match = re.search(
            r"METADATA:\s*\n(?P<metadata>\{[^\n]*\})",
            block,
)

        if not metadata_match:
            raise ValueError(
                f"Could not find METADATA "
                f"for CHUNK {chunk_index}."
            )

        metadata_raw = (
            metadata_match.group("metadata")
            .strip()
        )

        try:

            metadata = ast.literal_eval(
                metadata_raw
            )

        except (
            ValueError,
            SyntaxError,
        ) as exc:

            raise ValueError(
                f"Could not parse metadata "
                f"for CHUNK {chunk_index}."
            ) from exc

        if not isinstance(
            metadata,
            dict,
        ):
            raise ValueError(
                f"Metadata for CHUNK "
                f"{chunk_index} must be a dictionary."
            )

        # ==============================================================
        # Validate document_id
        # ==============================================================

        metadata_document_id = metadata.get(
            "document_id"
        )

        if metadata_document_id != document_id:
            raise ValueError(
                f"CHUNK {chunk_index} contains "
                f"document_id={metadata_document_id}, "
                f"but expected {document_id}."
            )

        # ==============================================================
        # Build FinalChunk
        # ==============================================================

        chunk = FinalChunk(
            text=text,
            elements=[],
            chunk_type=chunk_type,
            section_path=section_path,
            order_index=order_index,
            metadata=metadata,
        )

        chunks.append(chunk)

    # ==================================================================
    # Final validation
    # ==================================================================

    if len(chunks) != expected_count:
        raise ValueError(
            "Final chunk count mismatch. "
            f"Expected={expected_count}, "
            f"Parsed={len(chunks)}"
        )

    return chunks


# ======================================================================
# PARSER TEST
# ======================================================================


def test_load_final_chunks():
    """
    Verify that the actual FinalChunk output
    can be reconstructed correctly.
    """

    chunks = load_final_chunks(
        DEBUG_CHUNKS_FILE
    )

    for i, chunk in enumerate(chunks):
        print(
            f"CHUNK {i}: "
            f"section_path={chunk.section_path}, "
            f"order_index={chunk.order_index}"
        )

    # --------------------------------------------------------------
    # Count
    # --------------------------------------------------------------

    assert len(chunks) == 10

    # --------------------------------------------------------------
    # Document ID
    # --------------------------------------------------------------

    for chunk in chunks:

        assert (
            chunk.metadata["document_id"]
            == 17
        )

    # --------------------------------------------------------------
    # First chunk
    # --------------------------------------------------------------

    assert (
        chunks[0].order_index
        == 0
    )

    assert chunks[0].text.startswith(
        "Intellex Enterprise Knowledge Platform"
    )

    # --------------------------------------------------------------
    # Chunk 3 — Unicode
    # --------------------------------------------------------------

    assert chunks[3].text.startswith(
        "Unicode Test"
    )

    assert "こんにちは" in (
        chunks[3].text
    )

    assert "नमस्ते" in (
        chunks[3].text
    )

    assert "안녕하세요" in (
        chunks[3].text
    )

    assert "😀" in (
        chunks[3].text
    )

    # --------------------------------------------------------------
    # Last chunk
    # --------------------------------------------------------------

    assert (
        chunks[9].text
        == "This is the last paragraph."
    )


# ======================================================================
# REAL 6C INTEGRATION TEST
# ======================================================================


def test_real_final_chunks_to_pgvector(
    db,
    embedding_service,
):
    """
    Real 6C integration test.

    FinalChunk[]
        ↓
    BGE-M3
        ↓
    EmbeddingPipeline
        ↓
    DocumentChunk
        ↓
    PostgreSQL
        ↓
    pgvector
    """

    # ==================================================================
    # 1. Load real FinalChunk output
    # ==================================================================

    chunks = load_final_chunks(
        DEBUG_CHUNKS_FILE
    )

    assert chunks

    assert len(chunks) == 10

    # ==================================================================
    # 2. Extract document ID
    # ==================================================================

    document_id = (
        chunks[0]
        .metadata["document_id"]
    )

    assert document_id == 17

    # ==================================================================
    # 3. Validate input
    # ==================================================================

    for chunk in chunks:

        assert chunk.text

        assert chunk.metadata

        assert (
            chunk.metadata["document_id"]
            == document_id
        )

        assert isinstance(
            chunk.section_path,
            list,
        )

    # ==================================================================
    # 4. Verify Document exists
    # ==================================================================

    document = db.execute(
        select(Document)
        .where(
            Document.document_id
            == document_id
        )
    ).scalar_one_or_none()

    if document is None:
        pytest.fail(
            f"Document {document_id} does not exist "
            "in the database."
        )

    # ==================================================================
    # 5. Delete previous chunks inside test transaction
    # ==================================================================

    db.query(
        DocumentChunk
    ).filter(
        DocumentChunk.document_id
        == document_id
    ).delete(
        synchronize_session=False
    )

    db.flush()

    # ==================================================================
    # 6. Create real EmbeddingPipeline
    # ==================================================================

    pipeline = EmbeddingPipeline(
        embedding_service=embedding_service
    )

    # ==================================================================
    # 7. REAL BGE-M3 + PostgreSQL
    # ==================================================================

    persisted_chunks = pipeline.process(
        db=db,
        chunks=chunks,
    )

    # ==================================================================
    # 8. Number of chunks
    # ==================================================================

    assert len(
        persisted_chunks
    ) == 10

    # ==================================================================
    # 9. Validate generated chunks
    # ==================================================================

    for index, persisted in enumerate(
        persisted_chunks
    ):

        original = chunks[index]

        assert (
            persisted.document_id
            == document_id
        )

        assert (
            persisted.chunk_index
            == index
        )

        assert (
            persisted.chunk_text
            == original.text
        )

        assert (
            persisted.token_count
            > 0
        )

        assert (
            persisted.embedding
            is not None
        )

        assert (
            len(persisted.embedding)
            == 1024
        )

    # ==================================================================
    # 10. Verify chunk indexes
    # ==================================================================

    indexes = [
        chunk.chunk_index
        for chunk in persisted_chunks
    ]

    assert indexes == list(
        range(10)
    )

    # ==================================================================
    # 11. Verify metadata
    # ==================================================================

    for index, persisted in enumerate(
        persisted_chunks
    ):

        original = chunks[index]

        assert (
            persisted.metadata_json[
                "document_id"
            ]
            == document_id
        )

        assert (
            persisted.metadata_json[
                "section_path"
            ]
            == list(
                original.section_path
            )
        )

        assert (
            persisted.metadata_json[
                "chunk_type"
            ]
            == original.chunk_type.value
        )

    # ==================================================================
    # 12. Query database again
    # ==================================================================

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

    # ==================================================================
    # 13. Verify database count
    # ==================================================================

    assert len(
        stored_chunks
    ) == 10

    # ==================================================================
    # 14. Verify database values
    # ==================================================================

    for index, stored in enumerate(
        stored_chunks
    ):

        original = chunks[index]

        assert (
            stored.document_id
            == document_id
        )

        assert (
            stored.chunk_index
            == index
        )

        assert (
            stored.chunk_text
            == original.text
        )

        assert (
            stored.token_count
            > 0
        )

        assert (
            stored.embedding
            is not None
        )

        assert (
            len(stored.embedding)
            == 1024
        )

    # ==================================================================
    # 15. Verify vectors aren't identical
    # ==================================================================

    vectors = [
        stored.embedding
        for stored in stored_chunks
    ]

    for index in range(
        len(vectors) - 1
    ):

        assert (
            vectors[index]
            != vectors[index + 1]
        )

    # ==================================================================
    # 16. Verify Unicode survived
    # ==================================================================

    unicode_chunk = next(
        chunk
        for chunk in stored_chunks
        if "こんにちは"
        in chunk.chunk_text
    )

    assert "こんにちは" in (
        unicode_chunk.chunk_text
    )

    assert "नमस्ते" in (
        unicode_chunk.chunk_text
    )

    assert "안녕하세요" in (
        unicode_chunk.chunk_text
    )

    assert "😀" in (
        unicode_chunk.chunk_text
    )

    # ==================================================================
    # 17. Verify section_path survived
    # ==================================================================

    for index, stored in enumerate(
        stored_chunks
    ):

        assert (
            stored.metadata_json[
                "section_path"
            ]
            == chunks[index].section_path
        )