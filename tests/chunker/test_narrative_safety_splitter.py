import pytest

from app.dto.extracted_element import ExtractedElement
from app.dto.routed_chunk import RoutedChunk
from app.enums.chunk_type import ChunkType
from app.enums.element_type import ElementType
from app.services.chunking.recursive_splitter.narrative_safety_splitter import NarrativeSafetySplitter


# ============================================================
# HELPERS
# ============================================================

def make_paragraph(
    order_index: int,
    text: str,
    metadata: dict | None = None,
) -> ExtractedElement:

    return ExtractedElement(
        order_index=order_index,
        text=text,
        element_type=ElementType.PARAGRAPH,
        metadata=metadata or {},
    )


def make_narrative_routed_chunk(
    elements: list[ExtractedElement],
    section_path: list[str] | None = None,
) -> RoutedChunk:

    elements = sorted(
        elements,
        key=lambda element: element.order_index,
    )

    text = "\n\n".join(
        element.text.strip()
        for element in elements
        if element.text and element.text.strip()
    )

    return RoutedChunk(
        chunk_type=next(iter(ChunkType)),
        elements=elements,
        text=text,
        section_path=section_path or [],
        order_index=elements[0].order_index if elements else 0,
    )


# ============================================================
# 1. EMPTY INPUT
# ============================================================

def test_empty_elements_returns_empty():

    routed = RoutedChunk(
        chunk_type=next(iter(ChunkType)),
        elements=[],
        text=None,
        section_path=[],
        order_index=0,
    )

    splitter = NarrativeSafetySplitter()

    result = splitter.split(routed)

    assert result == []


def test_none_text_returns_empty():

    element = make_paragraph(
        order_index=1,
        text="Hello",
    )

    routed = RoutedChunk(
        chunk_type=next(iter(ChunkType)),
        elements=[element],
        text=None,
        section_path=[],
        order_index=1,
    )

    splitter = NarrativeSafetySplitter()

    result = splitter.split(routed)

    assert result == []


def test_empty_text_returns_empty():

    element = make_paragraph(
        order_index=1,
        text="Hello",
    )

    routed = RoutedChunk(
        chunk_type=next(iter(ChunkType)),
        elements=[element],
        text="",
        section_path=[],
        order_index=1,
    )

    splitter = NarrativeSafetySplitter()

    result = splitter.split(routed)

    assert result == []


def test_whitespace_only_text_returns_empty():

    element = make_paragraph(
        order_index=1,
        text="   ",
    )

    routed = RoutedChunk(
        chunk_type=next(iter(ChunkType)),
        elements=[element],
        text="   ",
        section_path=[],
        order_index=1,
    )

    splitter = NarrativeSafetySplitter()

    result = splitter.split(routed)

    assert result == []


# ============================================================
# 2. ALREADY FITS
# ============================================================

def test_small_chunk_is_returned_unchanged():

    element = make_paragraph(
        order_index=1,
        text="Hello world",
    )

    routed = make_narrative_routed_chunk(
        [element]
    )

    splitter = NarrativeSafetySplitter(
        max_tokens=1000
    )

    result = splitter.split(routed)

    assert len(result) == 1

    assert result[0].text == routed.text

    assert result[0].elements == routed.elements


def test_chunk_exactly_at_limit_fits():

    splitter = NarrativeSafetySplitter(
        max_tokens=10
    )

    text = "A" * 40

    element = make_paragraph(
        order_index=1,
        text=text,
    )

    routed = make_narrative_routed_chunk(
        [element]
    )

    result = splitter.split(routed)

    assert len(result) == 1
    assert result[0].text == text


def test_chunk_one_character_over_limit():

    splitter = NarrativeSafetySplitter(
        max_tokens=10
    )

    text = "A" * 41

    element = make_paragraph(
        order_index=1,
        text=text,
    )

    routed = make_narrative_routed_chunk(
        [element]
    )

    result = splitter.split(routed)

    assert len(result) >= 1

    reconstructed = "\n".join(
        chunk.text
        for chunk in result
    )

    assert reconstructed == text


# ============================================================
# 3. ELEMENT-BOUNDARY SPLITTING
# ============================================================

def test_multiple_elements_split_at_element_boundaries():

    elements = [
        make_paragraph(1, "A" * 100),
        make_paragraph(2, "B" * 100),
        make_paragraph(3, "C" * 100),
    ]

    routed = make_narrative_routed_chunk(
        elements
    )

    splitter = NarrativeSafetySplitter(
        max_tokens=50
    )

    chunks = splitter.split(routed)

    assert len(chunks) > 1

    flattened = [
        element.order_index
        for chunk in chunks
        for element in chunk.elements
    ]

    assert flattened == [1, 2, 3]


def test_elements_are_not_duplicated():

    elements = [
        make_paragraph(1, "A" * 100),
        make_paragraph(2, "B" * 100),
        make_paragraph(3, "C" * 100),
    ]

    routed = make_narrative_routed_chunk(elements)

    splitter = NarrativeSafetySplitter(
        max_tokens=50
    )

    chunks = splitter.split(routed)

    flattened = [
        element.order_index
        for chunk in chunks
        for element in chunk.elements
    ]

    assert flattened == [1, 2, 3]

    assert len(flattened) == len(
        set(flattened)
    )


def test_elements_are_not_lost():

    elements = [
        make_paragraph(1, "A" * 100),
        make_paragraph(2, "B" * 100),
        make_paragraph(3, "C" * 100),
    ]

    routed = make_narrative_routed_chunk(elements)

    splitter = NarrativeSafetySplitter(
        max_tokens=50
    )

    chunks = splitter.split(routed)

    original_ids = [
        element.order_index
        for element in elements
    ]

    chunked_ids = [
        element.order_index
        for chunk in chunks
        for element in chunk.elements
    ]

    assert chunked_ids == original_ids


def test_elements_remain_in_document_order():

    elements = [
        make_paragraph(3, "C" * 100),
        make_paragraph(1, "A" * 100),
        make_paragraph(2, "B" * 100),
    ]

    routed = make_narrative_routed_chunk(
        elements
    )

    splitter = NarrativeSafetySplitter(
        max_tokens=50
    )

    chunks = splitter.split(routed)

    flattened = [
        element.order_index
        for chunk in chunks
        for element in chunk.elements
    ]

    assert flattened == [1, 2, 3]


# ============================================================
# 4. SINGLE OVERSIZED ELEMENT
# ============================================================

def test_oversized_single_element_creates_fragments():

    element = make_paragraph(
        order_index=10,
        text="\n".join(
            f"line {i}"
            for i in range(200)
        ),
    )

    routed = make_narrative_routed_chunk(
        [element]
    )

    splitter = NarrativeSafetySplitter(
        max_tokens=10
    )

    chunks = splitter.split(routed)

    assert len(chunks) > 1

    reconstructed = "\n".join(
        chunk.text
        for chunk in chunks
    )

    assert reconstructed == element.text

    assert all(
        chunk.elements[0].metadata["safety_split"] is True
        for chunk in chunks
    )


def test_oversized_fragments_preserve_source_order_index():

    element = make_paragraph(
        order_index=10,
        text="\n".join(
            f"line {i}"
            for i in range(200)
        ),
    )

    routed = make_narrative_routed_chunk(
        [element]
    )

    splitter = NarrativeSafetySplitter(
        max_tokens=10
    )

    chunks = splitter.split(routed)

    assert all(
        chunk.elements[0].order_index == 10
        for chunk in chunks
    )


def test_oversized_fragments_have_source_metadata():

    element = make_paragraph(
        order_index=10,
        text="\n".join(
            f"line {i}"
            for i in range(200)
        ),
    )

    routed = make_narrative_routed_chunk(
        [element]
    )

    splitter = NarrativeSafetySplitter(
        max_tokens=10
    )

    chunks = splitter.split(routed)

    total_parts = len(chunks)

    for index, chunk in enumerate(chunks):

        metadata = chunk.elements[0].metadata

        assert metadata["safety_split"] is True

        assert (
            metadata["safety_split_part"]
            == index
        )

        assert (
            metadata["safety_split_total"]
            == total_parts
        )

        assert (
            metadata["safety_split_source_order_index"]
            == 10
        )


# ============================================================
# 5. LINE SPLITTING
# ============================================================

def test_40_lines_remain_one_fragment():

    text = "\n".join(
        f"line {i}"
        for i in range(40)
    )

    splitter = NarrativeSafetySplitter()

    parts = splitter._split_lines(
        text,
        max_lines=40,
    )

    assert len(parts) == 1
    assert parts[0] == text


def test_41_lines_create_two_fragments():

    text = "\n".join(
        f"line {i}"
        for i in range(41)
    )

    splitter = NarrativeSafetySplitter()

    parts = splitter._split_lines(
        text,
        max_lines=40,
    )

    assert len(parts) == 2

    assert "\n".join(parts) == text


def test_80_lines_create_two_fragments():

    text = "\n".join(
        f"line {i}"
        for i in range(80)
    )

    splitter = NarrativeSafetySplitter()

    parts = splitter._split_lines(
        text,
        max_lines=40,
    )

    assert len(parts) == 2

    assert "\n".join(parts) == text


def test_81_lines_create_three_fragments():

    text = "\n".join(
        f"line {i}"
        for i in range(81)
    )

    splitter = NarrativeSafetySplitter()

    parts = splitter._split_lines(
        text,
        max_lines=40,
    )

    assert len(parts) == 3

    assert "\n".join(parts) == text


# ============================================================
# 6. RECURSIVE SPLITTING
# ============================================================

def test_recursive_splitting_continues_until_safe():

    elements = [
        make_paragraph(
            1,
            "A" * 500,
        ),
        make_paragraph(
            2,
            "B" * 500,
        ),
        make_paragraph(
            3,
            "C" * 500,
        ),
        make_paragraph(
            4,
            "D" * 500,
        ),
    ]

    routed = make_narrative_routed_chunk(
        elements
    )

    splitter = NarrativeSafetySplitter(
        max_tokens=100
    )

    chunks = splitter.split(routed)

    assert len(chunks) >= 2

    for chunk in chunks:

        assert (
            len(chunk.text)
            <= 100 * 4
            or len(chunk.elements) == 1
        )


# ============================================================
# 7. WHITESPACE ELEMENTS
# ============================================================

def test_whitespace_elements_are_ignored():

    elements = [
        make_paragraph(
            1,
            "A" * 100,
        ),
        make_paragraph(
            2,
            "   ",
        ),
        make_paragraph(
            3,
            "\n\t",
        ),
        make_paragraph(
            4,
            "B" * 100,
        ),
    ]

    routed = make_narrative_routed_chunk(
        elements
    )

    splitter = NarrativeSafetySplitter(
        max_tokens=50
    )

    chunks = splitter.split(routed)

    flattened = [
        element.order_index
        for chunk in chunks
        for element in chunk.elements
    ]

    assert flattened == [1, 4]


# ============================================================
# 8. METADATA PRESERVATION
# ============================================================

def test_existing_metadata_is_preserved():

    element = make_paragraph(
        order_index=1,
        text="Hello",
        metadata={
            "document_id": "doc-123",
            "source": "report.pdf",
        },
    )

    routed = make_narrative_routed_chunk(
        [element]
    )

    splitter = NarrativeSafetySplitter()

    chunks = splitter.split(routed)

    metadata = chunks[0].elements[0].metadata

    assert metadata["document_id"] == "doc-123"
    assert metadata["source"] == "report.pdf"


def test_section_path_is_preserved():

    element = make_paragraph(
        order_index=1,
        text="Hello",
    )

    section_path = [
        "Chapter 1",
        "Introduction",
    ]

    routed = make_narrative_routed_chunk(
        [element],
        section_path=section_path,
    )

    splitter = NarrativeSafetySplitter()

    chunks = splitter.split(routed)

    assert chunks[0].section_path == section_path


# ============================================================
# 9. TEXT RECONSTRUCTION
# ============================================================

def test_multiple_element_text_is_reconstructed():

    elements = [
        make_paragraph(
            1,
            "First paragraph",
        ),
        make_paragraph(
            2,
            "Second paragraph",
        ),
        make_paragraph(
            3,
            "Third paragraph",
        ),
    ]

    routed = make_narrative_routed_chunk(
        elements
    )

    splitter = NarrativeSafetySplitter(
        max_tokens=1000
    )

    chunks = splitter.split(routed)

    assert len(chunks) == 1

    assert chunks[0].text == (
        "First paragraph\n\n"
        "Second paragraph\n\n"
        "Third paragraph"
    )


def test_single_element_text_is_preserved_exactly():

    text = (
        "This is a paragraph.\n"
        "With multiple lines.\n"
        "And some more content."
    )

    element = make_paragraph(
        order_index=1,
        text=text,
    )

    routed = make_narrative_routed_chunk(
        [element]
    )

    splitter = NarrativeSafetySplitter(
        max_tokens=1000
    )

    chunks = splitter.split(routed)

    assert len(chunks) == 1
    assert chunks[0].text == text


# ============================================================
# 10. SPECIAL CHARACTERS
# ============================================================

def test_special_characters_are_preserved():

    text = (
        "Hello 🚀\n"
        "Value: {'key': [1, 2, 3]}\n"
        "Path: C:\\Users\\Test\n"
        "Symbols: @#$%^&*"
    )

    element = make_paragraph(
        order_index=1,
        text=text,
    )

    routed = make_narrative_routed_chunk(
        [element]
    )

    splitter = NarrativeSafetySplitter()

    chunks = splitter.split(routed)

    assert chunks[0].text == text


# ============================================================
# 11. VERY LARGE SINGLE LINE
# ============================================================

def test_huge_single_line_does_not_crash():

    text = "A" * 50_000

    element = make_paragraph(
        order_index=1,
        text=text,
    )

    routed = make_narrative_routed_chunk(
        [element]
    )

    splitter = NarrativeSafetySplitter(
        max_tokens=100
    )

    chunks = splitter.split(routed)

    assert len(chunks) == 1

    assert chunks[0].text == text


# ============================================================
# 12. MIXED ELEMENT SIZES
# ============================================================

def test_mixed_element_sizes_are_split_safely():

    elements = [
        make_paragraph(
            1,
            "A" * 100,
        ),
        make_paragraph(
            2,
            "B" * 300,
        ),
        make_paragraph(
            3,
            "C" * 100,
        ),
        make_paragraph(
            4,
            "D" * 500,
        ),
    ]

    routed = make_narrative_routed_chunk(
        elements
    )

    splitter = NarrativeSafetySplitter(
        max_tokens=100
    )

    chunks = splitter.split(routed)

    assert chunks

    flattened = [
        element.order_index
        for chunk in chunks
        for element in chunk.elements
    ]

    assert flattened == [1, 2, 3, 4]


# ============================================================
# 13. NO DUPLICATION / NO LOSS IN FINAL OUTPUT
# ============================================================

def test_every_original_element_appears_exactly_once():

    elements = [
        make_paragraph(1, "A" * 100),
        make_paragraph(2, "B" * 100),
        make_paragraph(3, "C" * 100),
        make_paragraph(4, "D" * 100),
        make_paragraph(5, "E" * 100),
    ]

    routed = make_narrative_routed_chunk(
        elements
    )

    splitter = NarrativeSafetySplitter(
        max_tokens=50
    )

    chunks = splitter.split(routed)

    flattened = [
        element.order_index
        for chunk in chunks
        for element in chunk.elements
    ]

    assert flattened == [
        1,
        2,
        3,
        4,
        5,
    ]

    assert len(flattened) == len(
        elements
    )

    assert len(flattened) == len(
        set(flattened)
    )


# ============================================================
# 14. FRAGMENT METADATA IS UNIQUE
# ============================================================

def test_safety_split_parts_have_unique_part_indexes():

    element = make_paragraph(
        order_index=10,
        text="\n".join(
            f"line {i}"
            for i in range(200)
        ),
    )

    routed = make_narrative_routed_chunk(
        [element]
    )

    splitter = NarrativeSafetySplitter(
        max_tokens=10
    )

    chunks = splitter.split(routed)

    part_indexes = [
        chunk.elements[0].metadata[
            "safety_split_part"
        ]
        for chunk in chunks
    ]

    assert part_indexes == list(
        range(len(chunks))
    )


# ============================================================
# 15. FINAL INTEGRITY TEST
# ============================================================

def test_final_output_preserves_all_elements_and_content():

    elements = [
        make_paragraph(
            1,
            "A" * 100,
        ),
        make_paragraph(
            2,
            "B" * 100,
        ),
        make_paragraph(
            3,
            "C" * 100,
        ),
    ]

    routed = make_narrative_routed_chunk(
        elements
    )

    splitter = NarrativeSafetySplitter(
        max_tokens=50
    )

    chunks = splitter.split(routed)

    # Every original element appears once.
    flattened_ids = [
        element.order_index
        for chunk in chunks
        for element in chunk.elements
    ]

    assert flattened_ids == [1, 2, 3]

    # No duplicate original elements.
    assert len(flattened_ids) == len(
        set(flattened_ids)
    )

    # Every output chunk has content.
    assert all(
        chunk.text
        and chunk.text.strip()
        for chunk in chunks
    )

    # Output remains in document order.
    assert flattened_ids == sorted(
        flattened_ids
    )