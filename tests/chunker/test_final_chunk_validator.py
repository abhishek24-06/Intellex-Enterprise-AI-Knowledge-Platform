import pytest

from app.dto.extracted_element import ExtractedElement
from app.dto.final_chunk import FinalChunk

from app.enums.chunk_type import ChunkType
from app.enums.element_type import ElementType

from app.services.chunking.final_chunker_validator.validator import (
    FinalChunkValidator,
    FinalChunkValidationError,
)


# ============================================================
# Helpers
# ============================================================

def make_element(
    order_index: int,
    text: str = "element text",
    element_type: ElementType = ElementType.PARAGRAPH,
):
    return ExtractedElement(
        order_index=order_index,
        text=text,
        element_type=element_type,
        metadata={},
    )


def make_chunk(
    order_index: int,
    elements: list[ExtractedElement] | None = None,
    text: str = "chunk text",
    chunk_type: ChunkType = ChunkType.NARRATIVE,
    section_path: list[str] | None = None,
    metadata: dict | None = None,
):
    if elements is None:
        elements = [
            make_element(order_index)
        ]

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
def validator():
    return FinalChunkValidator()


# ============================================================
# 1. VALID CASES
# ============================================================

def test_valid_chunks_pass(validator):

    element_0 = make_element(0)
    element_1 = make_element(1)

    chunks = [
        make_chunk(
            order_index=0,
            elements=[element_0],
        ),
        make_chunk(
            order_index=1,
            elements=[element_1],
        ),
    ]

    validator.validate(
        chunks=chunks,
        source_elements=[element_0, element_1],
    )


def test_empty_chunk_collection_passes(validator):

    validator.validate(
        chunks=[]
    )


def test_empty_source_elements_pass(validator):

    validator.validate(
        chunks=[],
        source_elements=[],
    )


def test_all_supported_chunk_types_pass(validator):

    narrative_element = make_element(0)
    table_element = make_element(1)
    code_element = make_element(2)

    chunks = [
        make_chunk(
            order_index=0,
            elements=[narrative_element],
            chunk_type=ChunkType.NARRATIVE,
        ),
        make_chunk(
            order_index=1,
            elements=[table_element],
            chunk_type=ChunkType.TABLE,
        ),
        make_chunk(
            order_index=2,
            elements=[code_element],
            chunk_type=ChunkType.CODE,
        ),
    ]

    validator.validate(
        chunks=chunks,
        source_elements=[
            narrative_element,
            table_element,
            code_element,
        ],
    )


def test_valid_metadata_passes(validator):

    element = make_element(0)

    chunk = make_chunk(
        order_index=0,
        elements=[element],
        metadata={
            "document_id": "doc-123",
            "filename": "report.pdf",
            "page": 4,
            "source": "docling",
        },
    )

    validator.validate([chunk])


def test_valid_section_path_passes(validator):

    element = make_element(0)

    chunk = make_chunk(
        order_index=0,
        elements=[element],
        section_path=[
            "Architecture",
            "Retrieval",
            "Vector Search",
        ],
    )

    validator.validate([chunk])


# ============================================================
# 2. INVALID CHUNK OBJECT
# ============================================================

def test_non_final_chunk_is_rejected(validator):

    with pytest.raises(FinalChunkValidationError):

        validator.validate(
            chunks=["not a FinalChunk"]
        )


def test_none_chunk_is_rejected(validator):

    with pytest.raises(FinalChunkValidationError):

        validator.validate(
            chunks=[None]
        )


# ============================================================
# 3. TEXT VALIDATION
# ============================================================

def test_empty_text_rejected(validator):

    chunk = make_chunk(
        order_index=0,
        text="",
    )

    with pytest.raises(FinalChunkValidationError):

        validator.validate([chunk])


def test_whitespace_only_text_rejected(validator):

    chunk = make_chunk(
        order_index=0,
        text="   \n\t   ",
    )

    with pytest.raises(FinalChunkValidationError):

        validator.validate([chunk])


def test_non_empty_text_with_whitespace_passes(validator):

    chunk = make_chunk(
        order_index=0,
        text="  valid text  ",
    )

    validator.validate([chunk])


# ============================================================
# 4. ELEMENT VALIDATION
# ============================================================

def test_empty_elements_rejected(validator):

    chunk = make_chunk(
        order_index=0,
        elements=[],
    )

    with pytest.raises(FinalChunkValidationError):

        validator.validate([chunk])


def test_invalid_source_element_rejected(validator):

    chunk = make_chunk(
        order_index=0,
        elements=["not an ExtractedElement"],
    )

    with pytest.raises(FinalChunkValidationError):

        validator.validate([chunk])


def test_negative_element_order_rejected(validator):

    element = make_element(-1)

    chunk = make_chunk(
        order_index=-1,
        elements=[element],
    )

    with pytest.raises(FinalChunkValidationError):

        validator.validate([chunk])


def test_invalid_element_order_type_rejected(validator):

    element = make_element(0)

    # Deliberately corrupt the DTO after construction.
    element.order_index = "0"

    chunk = make_chunk(
        order_index=0,
        elements=[element],
    )

    with pytest.raises(FinalChunkValidationError):

        validator.validate([chunk])


# ============================================================
# 5. CHUNK TYPE VALIDATION
# ============================================================

def test_invalid_chunk_type_rejected(validator):

    chunk = make_chunk(
        order_index=0,
    )

    chunk.chunk_type = "NARRATIVE"

    with pytest.raises(FinalChunkValidationError):

        validator.validate([chunk])


def test_unsupported_chunk_type_rejected(validator):

    chunk = make_chunk(
        order_index=0,
    )

    class FakeChunkType:
        pass

    chunk.chunk_type = FakeChunkType()

    with pytest.raises(FinalChunkValidationError):

        validator.validate([chunk])


# ============================================================
# 6. SECTION PATH VALIDATION
# ============================================================

def test_section_path_must_be_list(validator):

    chunk = make_chunk(
        order_index=0,
    )

    chunk.section_path = "Architecture"

    with pytest.raises(FinalChunkValidationError):

        validator.validate([chunk])


def test_section_path_values_must_be_strings(validator):

    chunk = make_chunk(
        order_index=0,
        section_path=[
            "Architecture",
            123,
        ],
    )

    with pytest.raises(FinalChunkValidationError):

        validator.validate([chunk])


def test_empty_section_path_passes(validator):

    chunk = make_chunk(
        order_index=0,
        section_path=[],
    )

    validator.validate([chunk])


# ============================================================
# 7. METADATA VALIDATION
# ============================================================

def test_metadata_must_be_dict(validator):

    chunk = make_chunk(
        order_index=0,
    )

    chunk.metadata = "invalid metadata"

    with pytest.raises(FinalChunkValidationError):

        validator.validate([chunk])


def test_empty_metadata_passes(validator):

    chunk = make_chunk(
        order_index=0,
        metadata={},
    )

    validator.validate([chunk])


# ============================================================
# 8. CHUNK ORDER INDEX VALIDATION
# ============================================================

def test_negative_order_index_rejected(validator):

    chunk = make_chunk(
        order_index=-1,
    )

    with pytest.raises(FinalChunkValidationError):

        validator.validate([chunk])


def test_order_index_must_be_integer(validator):

    chunk = make_chunk(
        order_index=0,
    )

    chunk.order_index = "0"

    with pytest.raises(FinalChunkValidationError):

        validator.validate([chunk])


def test_unsorted_chunks_rejected(validator):

    element_10 = make_element(10)
    element_2 = make_element(2)

    chunks = [
        make_chunk(
            order_index=10,
            elements=[element_10],
        ),
        make_chunk(
            order_index=2,
            elements=[element_2],
        ),
    ]

    with pytest.raises(FinalChunkValidationError):

        validator.validate(chunks)


def test_equal_chunk_order_indexes_are_allowed(validator):

    element_5_a = make_element(5, "fragment one")
    element_5_b = make_element(5, "fragment two")

    chunks = [
        make_chunk(
            order_index=5,
            elements=[element_5_a],
        ),
        make_chunk(
            order_index=5,
            elements=[element_5_b],
        ),
    ]

    validator.validate(chunks)


# ============================================================
# 9. INTERNAL ELEMENT DUPLICATION
# ============================================================

def test_duplicate_element_inside_chunk_rejected(validator):

    element = make_element(5)

    chunk = make_chunk(
        order_index=5,
        elements=[
            element,
            element,
        ],
    )

    with pytest.raises(FinalChunkValidationError):

        validator.validate([chunk])


def test_two_different_elements_with_same_order_index_rejected(
    validator,
):

    element_a = make_element(
        5,
        "first",
    )

    element_b = make_element(
        5,
        "second",
    )

    chunk = make_chunk(
        order_index=5,
        elements=[
            element_a,
            element_b,
        ],
    )

    with pytest.raises(FinalChunkValidationError):

        validator.validate([chunk])


# ============================================================
# 10. CHUNK ORDER MUST MATCH FIRST SOURCE POSITION
# ============================================================

def test_chunk_order_must_match_first_source_element(validator):

    element_5 = make_element(5)
    element_8 = make_element(8)

    chunk = make_chunk(
        order_index=8,
        elements=[
            element_5,
            element_8,
        ],
    )

    with pytest.raises(FinalChunkValidationError):

        validator.validate([chunk])


def test_chunk_order_matches_minimum_source_order(validator):

    element_5 = make_element(5)
    element_8 = make_element(8)

    chunk = make_chunk(
        order_index=5,
        elements=[
            element_5,
            element_8,
        ],
    )

    validator.validate([chunk])


# ============================================================
# 11. SOURCE COVERAGE
# ============================================================

def test_missing_source_element_rejected(validator):

    element_0 = make_element(0)
    element_1 = make_element(1)
    element_2 = make_element(2)

    chunks = [
        make_chunk(
            order_index=0,
            elements=[element_0],
        ),
        make_chunk(
            order_index=2,
            elements=[element_2],
        ),
    ]

    source_elements = [
        element_0,
        element_1,
        element_2,
    ]

    with pytest.raises(FinalChunkValidationError):

        validator.validate(
            chunks=chunks,
            source_elements=source_elements,
        )


def test_all_source_elements_are_covered(validator):

    element_0 = make_element(0)
    element_1 = make_element(1)
    element_2 = make_element(2)

    chunks = [
        make_chunk(
            order_index=0,
            elements=[element_0],
        ),
        make_chunk(
            order_index=1,
            elements=[element_1],
        ),
        make_chunk(
            order_index=2,
            elements=[element_2],
        ),
    ]

    validator.validate(
        chunks=chunks,
        source_elements=[
            element_0,
            element_1,
            element_2,
        ],
    )


def test_source_coverage_ignores_heading_elements(
    validator,
):

    heading = make_element(
        0,
        "Introduction",
        ElementType.HEADING,
    )

    paragraph = make_element(
        1,
        "Important content",
        ElementType.PARAGRAPH,
    )

    chunk = make_chunk(
        order_index=1,
        elements=[paragraph],
        text="Important content",
        section_path=["Introduction"],
    )

    # The heading is intentionally not present in
    # chunk.elements. It is represented structurally through
    # section_path.
    validator.validate(
        chunks=[chunk],
        source_elements=[
            heading,
            paragraph,
        ],
    )


def test_missing_non_heading_source_element_is_rejected(
    validator,
):

    paragraph_1 = make_element(
        0,
        "Content 1",
        ElementType.PARAGRAPH,
    )

    paragraph_2 = make_element(
        1,
        "Content 2",
        ElementType.PARAGRAPH,
    )

    chunk = make_chunk(
        order_index=0,
        elements=[paragraph_1],
        text="Content 1",
    )

    with pytest.raises(FinalChunkValidationError):

        validator.validate(
            chunks=[chunk],
            source_elements=[
                paragraph_1,
                paragraph_2,
            ],
        )


def test_missing_heading_does_not_cause_source_coverage_failure(
    validator,
):

    heading_1 = make_element(
        0,
        "Introduction",
        ElementType.HEADING,
    )

    heading_2 = make_element(
        1,
        "Architecture",
        ElementType.HEADING,
    )

    paragraph = make_element(
        2,
        "Architecture explanation",
        ElementType.PARAGRAPH,
    )

    chunk = make_chunk(
        order_index=2,
        elements=[paragraph],
        text="Architecture explanation",
        section_path=["Architecture"],
    )

    # Neither heading is inside FinalChunk.elements.
    #
    # This is valid for source coverage because headings are
    # structural elements, not content elements.
    validator.validate(
        chunks=[chunk],
        source_elements=[
            heading_1,
            heading_2,
            paragraph,
        ],
    )


def test_all_content_elements_are_covered_even_with_headings(
    validator,
):

    heading = make_element(
        0,
        "Results",
        ElementType.HEADING,
    )

    paragraph_1 = make_element(
        1,
        "Result one",
        ElementType.PARAGRAPH,
    )

    paragraph_2 = make_element(
        2,
        "Result two",
        ElementType.PARAGRAPH,
    )

    chunks = [
        make_chunk(
            order_index=1,
            elements=[paragraph_1],
            text="Result one",
            section_path=["Results"],
        ),
        make_chunk(
            order_index=2,
            elements=[paragraph_2],
            text="Result two",
            section_path=["Results"],
        ),
    ]

    validator.validate(
        chunks=chunks,
        source_elements=[
            heading,
            paragraph_1,
            paragraph_2,
        ],
    )


def test_source_coverage_is_optional(validator):

    element = make_element(0)

    chunk = make_chunk(
        order_index=0,
        elements=[element],
    )

    # No source_elements supplied.
    validator.validate([chunk])


# ============================================================
# 12. LEGITIMATE SAFETY-SPLIT BEHAVIOR
# ============================================================

def test_same_source_element_can_appear_in_multiple_split_chunks(
    validator,
):

    original_element = make_element(
        5,
        "large paragraph",
    )

    chunk_1 = make_chunk(
        order_index=5,
        elements=[original_element],
        text="fragment one",
    )

    chunk_2 = make_chunk(
        order_index=5,
        elements=[original_element],
        text="fragment two",
    )

    chunk_3 = make_chunk(
        order_index=5,
        elements=[original_element],
        text="fragment three",
    )

    validator.validate(
        chunks=[
            chunk_1,
            chunk_2,
            chunk_3,
        ],
        source_elements=[
            original_element,
        ],
    )


def test_split_fragments_with_same_order_index_are_allowed(
    validator,
):

    original_element = make_element(
        10,
        "large paragraph",
    )

    chunks = [
        make_chunk(
            order_index=10,
            elements=[original_element],
            text="part 1",
        ),
        make_chunk(
            order_index=10,
            elements=[original_element],
            text="part 2",
        ),
    ]

    validator.validate(chunks)


# ============================================================
# 13. MIXED REALISTIC FINAL CHUNKS
# ============================================================

def test_realistic_mixed_document_passes(validator):

    paragraph = make_element(
        0,
        "This is a narrative paragraph.",
        ElementType.PARAGRAPH,
    )

    table = make_element(
        2,
        "A | B\n1 | 2",
        ElementType.TABLE,
    )

    code = make_element(
        4,
        "print('hello')",
        ElementType.CODE_BLOCK,
    )

    chunks = [
        make_chunk(
            order_index=0,
            elements=[paragraph],
            chunk_type=ChunkType.NARRATIVE,
            metadata={
                "document_id": "doc-1",
                "page": 1,
            },
        ),
        make_chunk(
            order_index=2,
            elements=[table],
            chunk_type=ChunkType.TABLE,
            metadata={
                "document_id": "doc-1",
                "page": 2,
            },
        ),
        make_chunk(
            order_index=4,
            elements=[code],
            chunk_type=ChunkType.CODE,
            metadata={
                "document_id": "doc-1",
                "page": 3,
                "language": "python",
            },
        ),
    ]

    validator.validate(
        chunks=chunks,
        source_elements=[
            paragraph,
            table,
            code,
        ],
    )