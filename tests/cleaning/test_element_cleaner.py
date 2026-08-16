from app.dto.extracted_element import (
    ExtractedElement,
)

from app.dto.extraction_result import (
    ExtractionResult,
)

from app.enums.element_type import (
    ElementType,
)

from app.services.cleaning.element_cleaner import (
    ElementCleaner,
)


# ============================================================================
# HELPERS
# ============================================================================

def make_element(
    order_index: int,
    text: str,
    element_type: ElementType,
    metadata: dict | None = None,
) -> ExtractedElement:

    return ExtractedElement(
        order_index=order_index,
        text=text,
        element_type=element_type,
        metadata=metadata or {},
    )


# ============================================================================
# EMPTY RESULT
# ============================================================================

def test_empty_extraction_result_returns_empty_result():

    result = ExtractionResult(
        elements=[]
    )

    cleaner = ElementCleaner()

    cleaned = cleaner.clean(
        result
    )

    assert isinstance(
        cleaned,
        ExtractionResult,
    )

    assert cleaned.elements == []


# ============================================================================
# NARRATIVE CLEANING
# ============================================================================

def test_narrative_text_is_cleaned():

    element = make_element(
        order_index=0,
        text=(
            "  Hello\t\tworld  \r\n"
            "\r\n"
            "\r\n"
            "This is a paragraph.   "
        ),
        element_type=ElementType.PARAGRAPH,
    )

    result = ExtractionResult(
        elements=[element]
    )

    cleaner = ElementCleaner()

    cleaned = cleaner.clean(
        result
    )

    assert cleaned.elements[0].text == (
        "Hello world\n\n"
        "This is a paragraph."
    )


# ============================================================================
# HEADING
# ============================================================================

def test_heading_uses_narrative_cleaning():

    element = make_element(
        order_index=0,
        text="\t  Chapter 1   \r\n",
        element_type=ElementType.HEADING,
        metadata={
            "level": 1,
        },
    )

    result = ExtractionResult(
        elements=[element]
    )

    cleaned = ElementCleaner().clean(
        result
    )

    assert cleaned.elements[0].text == (
        "Chapter 1"
    )


# ============================================================================
# LIST
# ============================================================================

def test_list_uses_narrative_cleaning():

    element = make_element(
        order_index=0,
        text="\t  First item   ",
        element_type=ElementType.LIST,
        metadata={
            "ordered": True,
        },
    )

    result = ExtractionResult(
        elements=[element]
    )

    cleaned = ElementCleaner().clean(
        result
    )

    assert cleaned.elements[0].text == (
        "First item"
    )


# ============================================================================
# QUOTE
# ============================================================================

def test_quote_uses_narrative_cleaning():

    element = make_element(
        order_index=0,
        text=(
            "  Important statement\t\r\n"
            "\r\n"
            "\r\n"
        ),
        element_type=ElementType.QUOTE,
    )

    result = ExtractionResult(
        elements=[element]
    )

    cleaned = ElementCleaner().clean(
        result
    )

    assert cleaned.elements[0].text == (
        "Important statement"
    )


# ============================================================================
# CODE — CRITICAL
# ============================================================================

def test_code_preserves_indentation():

    code = (
        "def hello():\r\n"
        "\tif True:\r\n"
        "\t\tprint('hello')\r\n"
        "\r\n"
        "\treturn True\r\n"
    )

    element = make_element(
        order_index=0,
        text=code,
        element_type=ElementType.CODE_BLOCK,
        metadata={
            "language": "python",
        },
    )

    result = ExtractionResult(
        elements=[element]
    )

    cleaned = ElementCleaner().clean(
        result
    )

    assert cleaned.elements[0].text == (
        "def hello():\n"
        "\tif True:\n"
        "\t\tprint('hello')\n"
        "\n"
        "\treturn True\n"
    )


# ============================================================================
# CODE — TABS MUST NOT BECOME SPACES
# ============================================================================

def test_code_tabs_are_not_collapsed():

    code = (
        "\tdef test():\n"
        "\t\treturn True"
    )

    element = make_element(
        order_index=0,
        text=code,
        element_type=ElementType.CODE_BLOCK,
    )

    result = ExtractionResult(
        elements=[element]
    )

    cleaned = ElementCleaner().clean(
        result
    )

    assert "\t" in (
        cleaned.elements[0].text
    )

    assert cleaned.elements[0].text == code


# ============================================================================
# TABLE
# ============================================================================

def test_table_text_is_cleaned_conservatively():

    element = make_element(
        order_index=0,
        text=(
            "A | B   \r\n"
            "1 | 2   \r\n"
        ),
        element_type=ElementType.TABLE,
        metadata={
            "cells": [
                ["A", "B"],
                ["1", "2"],
            ],
            "n_rows": 2,
            "n_cols": 2,
            "has_header_row": True,
        },
    )

    result = ExtractionResult(
        elements=[element]
    )

    cleaned = ElementCleaner().clean(
        result
    )

    assert cleaned.elements[0].text == (
        "A | B\n"
        "1 | 2\n"
    )


# ============================================================================
# METADATA PRESERVATION
# ============================================================================

def test_metadata_is_preserved():

    metadata = {
        "document_id": "doc-1",
        "filename": "report.pdf",
        "source": "docling",
        "page": 4,
        "bbox": (
            10.0,
            20.0,
            30.0,
            40.0,
        ),
    }

    element = make_element(
        order_index=7,
        text="  Hello  ",
        element_type=ElementType.PARAGRAPH,
        metadata=metadata,
    )

    result = ExtractionResult(
        elements=[element]
    )

    cleaned = ElementCleaner().clean(
        result
    )

    assert cleaned.elements[0].metadata == (
        metadata
    )


# ============================================================================
# METADATA MUST NOT SHARE THE SAME DICT
# ============================================================================

def test_metadata_is_copied_not_shared():

    metadata = {
        "document_id": "doc-1",
        "source": "docling",
    }

    element = make_element(
        order_index=0,
        text="Hello",
        element_type=ElementType.PARAGRAPH,
        metadata=metadata,
    )

    result = ExtractionResult(
        elements=[element]
    )

    cleaned = ElementCleaner().clean(
        result
    )

    cleaned.elements[0].metadata[
        "new_field"
    ] = "value"

    assert (
        "new_field"
        not in element.metadata
    )


# ============================================================================
# SOURCE ELEMENT MUST NOT BE MUTATED
# ============================================================================

def test_original_element_is_not_mutated():

    element = make_element(
        order_index=5,
        text="  Hello\tworld  ",
        element_type=ElementType.PARAGRAPH,
        metadata={
            "source": "txt",
        },
    )

    original_text = element.text
    original_metadata = dict(
        element.metadata
    )

    result = ExtractionResult(
        elements=[element]
    )

    cleaned = ElementCleaner().clean(
        result
    )

    assert element.text == original_text

    assert (
        element.metadata
        == original_metadata
    )

    assert (
        cleaned.elements[0]
        is not element
    )


# ============================================================================
# ORDER INDEX PRESERVATION
# ============================================================================

def test_order_index_is_preserved():

    elements = [
        make_element(
            10,
            " First ",
            ElementType.PARAGRAPH,
        ),
        make_element(
            20,
            " Second ",
            ElementType.HEADING,
        ),
        make_element(
            30,
            "print(True)",
            ElementType.CODE_BLOCK,
        ),
    ]

    result = ExtractionResult(
        elements=elements
    )

    cleaned = ElementCleaner().clean(
        result
    )

    assert [
        element.order_index
        for element in cleaned.elements
    ] == [
        10,
        20,
        30,
    ]


# ============================================================================
# ELEMENT TYPE PRESERVATION
# ============================================================================

def test_element_type_is_preserved():

    elements = [
        make_element(
            0,
            "Title",
            ElementType.TITLE,
        ),
        make_element(
            1,
            "Heading",
            ElementType.HEADING,
        ),
        make_element(
            2,
            "Paragraph",
            ElementType.PARAGRAPH,
        ),
        make_element(
            3,
            "List",
            ElementType.LIST,
        ),
        make_element(
            4,
            "Quote",
            ElementType.QUOTE,
        ),
        make_element(
            5,
            "Code",
            ElementType.CODE_BLOCK,
        ),
        make_element(
            6,
            "Table",
            ElementType.TABLE,
        ),
    ]

    result = ExtractionResult(
        elements=elements
    )

    cleaned = ElementCleaner().clean(
        result
    )

    assert [
        element.element_type
        for element in cleaned.elements
    ] == [
        ElementType.TITLE,
        ElementType.HEADING,
        ElementType.PARAGRAPH,
        ElementType.LIST,
        ElementType.QUOTE,
        ElementType.CODE_BLOCK,
        ElementType.TABLE,
    ]


# ============================================================================
# NO ELEMENTS ARE DROPPED
# ============================================================================

def test_cleaner_does_not_drop_empty_elements():

    elements = [
        make_element(
            0,
            "",
            ElementType.PARAGRAPH,
        ),
        make_element(
            1,
            "   ",
            ElementType.PARAGRAPH,
        ),
        make_element(
            2,
            "Actual content",
            ElementType.PARAGRAPH,
        ),
    ]

    result = ExtractionResult(
        elements=elements
    )

    cleaned = ElementCleaner().clean(
        result
    )

    assert len(
        cleaned.elements
    ) == 3

    assert [
        element.order_index
        for element in cleaned.elements
    ] == [
        0,
        1,
        2,
    ]


# ============================================================================
# INVALID INPUT
# ============================================================================

def test_clean_rejects_invalid_extraction_result():

    cleaner = ElementCleaner()

    try:
        cleaner.clean("invalid")
    except TypeError as exc:
        assert (
            "ExtractionResult"
            in str(exc)
        )
    else:
        raise AssertionError(
            "Expected TypeError"
        )


