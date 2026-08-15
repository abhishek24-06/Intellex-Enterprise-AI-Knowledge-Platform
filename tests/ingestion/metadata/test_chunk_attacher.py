import copy

import pytest

from app.dto.chunk_context import ChunkContext
from app.dto.final_chunk import FinalChunk
from app.enums.enums import DocumentVisibility
from app.services.ingestion.metadata.chunk_attacher import ChunkContextAttacher


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_context(
    document_id=100,
    organization_id=200,
    uploaded_by=300,
    document_version=1,
):
    """
    Create a valid ChunkContext without depending on a specific
    DocumentVisibility enum member name.
    """
    visibility = next(iter(DocumentVisibility))

    return ChunkContext(
        document_id=document_id,
        organization_id=organization_id,
        uploaded_by=uploaded_by,
        visibility=visibility,
        document_version=document_version,
    )


def make_chunk(
    text="Sample chunk text",
    elements=None,
    chunk_type="text",
    section_path=None,
    order_index=0,
    metadata=None,
):
    """
    Create a FinalChunk for testing.
    """
    if elements is None:
        elements = []

    if section_path is None:
        section_path = []

    if metadata is None:
        metadata = {}

    return FinalChunk(
        text=text,
        elements=elements,
        chunk_type=chunk_type,
        section_path=section_path,
        order_index=order_index,
        metadata=metadata,
    )


@pytest.fixture
def attacher():
    return ChunkContextAttacher()


@pytest.fixture
def context():
    return make_context()


# ---------------------------------------------------------------------------
# 1. Empty chunks -> empty list
# ---------------------------------------------------------------------------

def test_empty_chunks_returns_empty_list(attacher, context):
    result = attacher.attach([], context)

    assert result == []
    assert isinstance(result, list)


# ---------------------------------------------------------------------------
# 2. Attaches all five context fields
# ---------------------------------------------------------------------------

def test_attaches_all_five_context_fields(attacher, context):
    chunk = make_chunk()

    result = attacher.attach([chunk], context)

    assert len(result) == 1

    metadata = result[0].metadata

    assert metadata["document_id"] == context.document_id
    assert metadata["organization_id"] == context.organization_id
    assert metadata["uploaded_by"] == context.uploaded_by
    assert metadata["visibility"] == context.visibility.value
    assert metadata["document_version"] == context.document_version


# ---------------------------------------------------------------------------
# 3. Attaches context to every chunk
# ---------------------------------------------------------------------------

def test_attaches_context_to_every_chunk(attacher, context):
    chunks = [
        make_chunk(
            text="First chunk",
            order_index=0,
        ),
        make_chunk(
            text="Second chunk",
            order_index=1,
        ),
        make_chunk(
            text="Third chunk",
            order_index=2,
        ),
        make_chunk(
            text="Fourth chunk",
            order_index=3,
        ),
    ]

    result = attacher.attach(chunks, context)

    assert len(result) == len(chunks)

    for chunk in result:
        assert chunk.metadata["document_id"] == context.document_id
        assert chunk.metadata["organization_id"] == context.organization_id
        assert chunk.metadata["uploaded_by"] == context.uploaded_by
        assert chunk.metadata["visibility"] == context.visibility.value
        assert chunk.metadata["document_version"] == context.document_version


# ---------------------------------------------------------------------------
# 4. Existing extractor metadata is preserved
# ---------------------------------------------------------------------------

def test_existing_extractor_metadata_is_preserved(attacher, context):
    chunk = make_chunk(
        metadata={
            "page_number": 5,
            "source": "report.pdf",
            "element_id": "element-123",
            "heading": "Introduction",
        }
    )

    result = attacher.attach([chunk], context)

    metadata = result[0].metadata

    assert metadata["page_number"] == 5
    assert metadata["source"] == "report.pdf"
    assert metadata["element_id"] == "element-123"
    assert metadata["heading"] == "Introduction"


# ---------------------------------------------------------------------------
# 5. Context overrides conflicting document_id
# ---------------------------------------------------------------------------

def test_context_overrides_conflicting_document_id(attacher, context):
    chunk = make_chunk(
        metadata={
            "document_id": 999999,
            "organization_id": 888888,
            "uploaded_by": 777777,
            "visibility": "incorrect_visibility",
            "document_version": 999,
        }
    )

    result = attacher.attach([chunk], context)

    metadata = result[0].metadata

    assert metadata["document_id"] == context.document_id
    assert metadata["organization_id"] == context.organization_id
    assert metadata["uploaded_by"] == context.uploaded_by
    assert metadata["visibility"] == context.visibility.value
    assert metadata["document_version"] == context.document_version


# ---------------------------------------------------------------------------
# 6. Original chunks are not mutated
# ---------------------------------------------------------------------------

def test_original_chunks_are_not_mutated(attacher, context):
    chunks = [
        make_chunk(
            text="First",
            section_path=["Chapter 1"],
            order_index=0,
            metadata={
                "page_number": 1,
                "document_id": 999,
            },
        ),
        make_chunk(
            text="Second",
            section_path=["Chapter 2"],
            order_index=1,
            metadata={
                "page_number": 2,
            },
        ),
    ]

    original_chunks = copy.deepcopy(chunks)

    result = attacher.attach(chunks, context)

    assert chunks == original_chunks

    # Explicitly verify that the original metadata did not receive
    # document-level context.
    assert "organization_id" not in chunks[0].metadata
    assert "uploaded_by" not in chunks[0].metadata
    assert "document_version" not in chunks[0].metadata


# ---------------------------------------------------------------------------
# 7. Core chunk fields remain unchanged
# ---------------------------------------------------------------------------

def test_chunk_content_fields_remain_unchanged(attacher, context):
    elements = [
        {
            "type": "paragraph",
            "text": "Important paragraph",
        },
        {
            "type": "table",
            "id": "table-1",
        },
    ]

    section_path = [
        "Chapter 1",
        "Section 1.2",
        "Subsection A",
    ]

    chunk = make_chunk(
        text="This is the original chunk text.",
        elements=elements,
        chunk_type="structured",
        section_path=section_path,
        order_index=42,
        metadata={
            "page_number": 10,
        },
    )

    result = attacher.attach([chunk], context)
    attached = result[0]

    assert attached.text == chunk.text
    assert attached.elements == chunk.elements
    assert attached.chunk_type == chunk.chunk_type
    assert attached.section_path == chunk.section_path
    assert attached.order_index == chunk.order_index


# ---------------------------------------------------------------------------
# Additional check:
# section_path should be copied rather than sharing the same list object
# ---------------------------------------------------------------------------

def test_section_path_is_not_same_list_object(attacher, context):
    section_path = ["Chapter 1", "Section 1"]

    chunk = make_chunk(
        section_path=section_path,
    )

    result = attacher.attach([chunk], context)

    attached = result[0]

    assert attached.section_path == section_path
    assert attached.section_path is not section_path


# ---------------------------------------------------------------------------
# 8. DocumentVisibility is stored consistently as enum value
# ---------------------------------------------------------------------------

def test_visibility_is_stored_as_enum_value(attacher):
    visibility = next(iter(DocumentVisibility))

    context = ChunkContext(
        document_id=100,
        organization_id=200,
        uploaded_by=300,
        visibility=visibility,
        document_version=1,
    )

    chunk = make_chunk()

    result = attacher.attach([chunk], context)

    stored_visibility = result[0].metadata["visibility"]

    # The attacher should store the enum's underlying value,
    # not the enum member itself.
    assert stored_visibility == visibility.value
    assert isinstance(stored_visibility, str)

# ---------------------------------------------------------------------------
# 9. Multiple chunks receive identical document-level context
# ---------------------------------------------------------------------------

def test_multiple_chunks_receive_identical_document_context(attacher, context):
    chunks = [
        make_chunk(text="Chunk A", order_index=0),
        make_chunk(text="Chunk B", order_index=1),
        make_chunk(text="Chunk C", order_index=2),
        make_chunk(text="Chunk D", order_index=3),
        make_chunk(text="Chunk E", order_index=4),
    ]

    result = attacher.attach(chunks, context)

    expected_context = {
        "document_id": context.document_id,
        "organization_id": context.organization_id,
        "uploaded_by": context.uploaded_by,
        "visibility": context.visibility.value,
        "document_version": context.document_version,
    }

    for attached_chunk in result:
        for key, expected_value in expected_context.items():
            assert attached_chunk.metadata[key] == expected_value


# ---------------------------------------------------------------------------
# EDGE CASE 1:
# Context values of zero should still be attached correctly
# ---------------------------------------------------------------------------

def test_zero_context_values_are_preserved(attacher):
    context = make_context(
        document_id=0,
        organization_id=0,
        uploaded_by=0,
        document_version=0,
    )

    chunk = make_chunk()

    result = attacher.attach([chunk], context)

    metadata = result[0].metadata

    assert metadata["document_id"] == 0
    assert metadata["organization_id"] == 0
    assert metadata["uploaded_by"] == 0
    assert metadata["document_version"] == 0
    assert metadata["visibility"] == context.visibility.value


# ---------------------------------------------------------------------------
# EDGE CASE 2:
# Empty metadata should work
# ---------------------------------------------------------------------------

def test_empty_metadata_is_handled(attacher, context):
    chunk = make_chunk(metadata={})

    result = attacher.attach([chunk], context)

    assert result[0].metadata == {
        "document_id": context.document_id,
        "organization_id": context.organization_id,
        "uploaded_by": context.uploaded_by,
        "visibility": context.visibility.value,
        "document_version": context.document_version,
    }


# ---------------------------------------------------------------------------
# EDGE CASE 3:
# Empty section_path should remain empty
# ---------------------------------------------------------------------------

def test_empty_section_path_is_preserved(attacher, context):
    chunk = make_chunk(
        section_path=[],
    )

    result = attacher.attach([chunk], context)

    assert result[0].section_path == []
    assert result[0].section_path is not chunk.section_path


# ---------------------------------------------------------------------------
# EDGE CASE 4:
# Empty text should remain unchanged
# ---------------------------------------------------------------------------

def test_empty_text_is_preserved(attacher, context):
    chunk = make_chunk(
        text="",
    )

    result = attacher.attach([chunk], context)

    assert result[0].text == ""


# ---------------------------------------------------------------------------
# EDGE CASE 5:
# None-like metadata values should be preserved
# ---------------------------------------------------------------------------

def test_existing_metadata_values_are_preserved_even_when_none(attacher, context):
    chunk = make_chunk(
        metadata={
            "page_number": None,
            "source": None,
            "custom_field": None,
        }
    )

    result = attacher.attach([chunk], context)

    metadata = result[0].metadata

    assert metadata["page_number"] is None
    assert metadata["source"] is None
    assert metadata["custom_field"] is None


# ---------------------------------------------------------------------------
# EDGE CASE 6:
# Different chunks can have different extractor metadata,
# while receiving identical document context.
# ---------------------------------------------------------------------------

def test_different_chunk_metadata_is_preserved_independently(
    attacher,
    context,
):
    chunks = [
        make_chunk(
            text="Chunk 1",
            metadata={
                "page_number": 1,
                "element_id": "p1",
            },
        ),
        make_chunk(
            text="Chunk 2",
            metadata={
                "page_number": 5,
                "element_id": "p5",
            },
        ),
    ]

    result = attacher.attach(chunks, context)

    assert result[0].metadata["page_number"] == 1
    assert result[0].metadata["element_id"] == "p1"

    assert result[1].metadata["page_number"] == 5
    assert result[1].metadata["element_id"] == "p5"

    assert result[0].metadata["document_id"] == context.document_id
    assert result[1].metadata["document_id"] == context.document_id


# ---------------------------------------------------------------------------
# EDGE CASE 7:
# Result should contain new FinalChunk objects rather than the originals
# ---------------------------------------------------------------------------

def test_attached_chunks_are_new_objects(attacher, context):
    chunks = [
        make_chunk(text="First"),
        make_chunk(text="Second"),
    ]

    result = attacher.attach(chunks, context)

    assert result[0] is not chunks[0]
    assert result[1] is not chunks[1]


# ---------------------------------------------------------------------------
# EDGE CASE 8:
# Metadata dictionary should not be shared with the original chunk
# ---------------------------------------------------------------------------

def test_metadata_is_not_shared_with_original_chunk(attacher, context):
    original_metadata = {
        "page_number": 10,
        "source": "document.pdf",
    }

    chunk = make_chunk(
        metadata=original_metadata,
    )

    result = attacher.attach([chunk], context)

    attached = result[0]

    assert attached.metadata is not chunk.metadata

    # Mutating the attached metadata must not mutate the original metadata.
    attached.metadata["new_field"] = "new_value"

    assert "new_field" not in chunk.metadata


# ---------------------------------------------------------------------------
# EDGE CASE 9:
# A large number of chunks should all receive context
# ---------------------------------------------------------------------------

def test_large_number_of_chunks_receive_context(attacher, context):
    chunks = [
        make_chunk(
            text=f"Chunk {i}",
            order_index=i,
        )
        for i in range(1000)
    ]

    result = attacher.attach(chunks, context)

    assert len(result) == 1000

    for chunk in result:
        assert chunk.metadata["document_id"] == context.document_id
        assert chunk.metadata["organization_id"] == context.organization_id
        assert chunk.metadata["uploaded_by"] == context.uploaded_by
        assert chunk.metadata["visibility"] == context.visibility.value
        assert chunk.metadata["document_version"] == context.document_version


# ---------------------------------------------------------------------------
# EDGE CASE 10:
# Ordering of chunks should remain unchanged
# ---------------------------------------------------------------------------

def test_chunk_order_is_preserved(attacher, context):
    chunks = [
        make_chunk(text="Third", order_index=2),
        make_chunk(text="First", order_index=0),
        make_chunk(text="Second", order_index=1),
    ]

    result = attacher.attach(chunks, context)

    assert [chunk.text for chunk in result] == [
        "Third",
        "First",
        "Second",
    ]

    assert [chunk.order_index for chunk in result] == [
        2,
        0,
        1,
    ]