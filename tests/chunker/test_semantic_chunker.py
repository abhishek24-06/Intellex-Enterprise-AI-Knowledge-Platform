import pytest

from app.dto.boundary_response import BoundaryResponse
from app.dto.extracted_element import ExtractedElement
from app.dto.extraction_result import ExtractionResult
from app.enums.element_type import ElementType
from app.services.chunking.llm_chunker.semantic_chunker import SemanticChunker


# =========================================================
# MOCK CLIENTS
# =========================================================

class MockLLMClient:

    def __init__(self, boundaries):
        self.boundaries = boundaries

    def detect_boundaries(self, prompt):

        return BoundaryResponse(
            boundaries=self.boundaries
        )


class FailingLLMClient:

    def detect_boundaries(self, prompt):

        raise RuntimeError("Gemini unavailable")


# =========================================================
# HELPER
# =========================================================

def make_element(
    order_index,
    text,
    element_type
):

    return ExtractedElement(
        order_index=order_index,
        text=text,
        element_type=element_type,
    )


# =========================================================
# TEST 1
# Multiple semantic boundaries
# =========================================================

def test_multiple_semantic_boundaries():

    elements = [
        make_element(
            0,
            "Paragraph 0",
            ElementType.PARAGRAPH
        ),

        make_element(
            1,
            "Paragraph 1",
            ElementType.PARAGRAPH
        ),

        make_element(
            2,
            "Paragraph 2",
            ElementType.PARAGRAPH
        ),

        make_element(
            3,
            "Paragraph 3",
            ElementType.PARAGRAPH
        ),

        make_element(
            4,
            "Paragraph 4",
            ElementType.PARAGRAPH
        ),

        make_element(
            5,
            "Paragraph 5",
            ElementType.PARAGRAPH
        ),
    ]

    extraction_result = ExtractionResult(
        elements=elements
    )

    mock_llm = MockLLMClient(
        boundaries=[0, 3, 5]
    )

    chunker = SemanticChunker(
        llm_client=mock_llm
    )

    candidates = chunker.chunk(
        extraction_result
    )

    assert len(candidates) == 3

    assert candidates[0].text == (
        "Paragraph 0\n\n"
        "Paragraph 1\n\n"
        "Paragraph 2"
    )

    assert candidates[1].text == (
        "Paragraph 3\n\n"
        "Paragraph 4"
    )

    assert candidates[2].text == "Paragraph 5"


# =========================================================
# TEST 2
# Table and code remain in elements
# but NOT in text
# =========================================================

def test_table_and_code_are_preserved_but_not_in_text():

    original_elements = [
        make_element(
            0,
            "Paragraph 0",
            ElementType.PARAGRAPH
        ),

        make_element(
            1,
            "Paragraph 1",
            ElementType.PARAGRAPH
        ),

        make_element(
            2,
            "table content",
            ElementType.TABLE
        ),

        make_element(
            3,
            "Paragraph 3",
            ElementType.PARAGRAPH
        ),

        make_element(
            4,
            "code content",
            ElementType.CODE_BLOCK
        ),

        make_element(
            5,
            "Paragraph 5",
            ElementType.PARAGRAPH
        ),
    ]

    extraction_result = ExtractionResult(
        elements=original_elements
    )

    mock_llm = MockLLMClient(
        boundaries=[0, 5]
    )

    chunker = SemanticChunker(
        llm_client=mock_llm
    )

    candidates = chunker.chunk(
        extraction_result
    )

    assert len(candidates) == 2

    first_candidate = candidates[0]

    # All original elements remain
    assert [
        element.order_index
        for element in first_candidate.elements
    ] == [0, 1, 2, 3, 4]

    table = original_elements[2]
    code = original_elements[4]

    # Table remains
    assert table in first_candidate.elements

    # Code remains
    assert code in first_candidate.elements

    # Table/code do NOT enter narrative text
    assert table.text not in first_candidate.text
    assert code.text not in first_candidate.text

    assert first_candidate.text == (
        "Paragraph 0\n\n"
        "Paragraph 1\n\n"
        "Paragraph 3"
    )


# =========================================================
# TEST 3
# Invalid boundary [999]
# =========================================================

def test_invalid_boundary_uses_fallback():

    original_elements = [
        make_element(
            0,
            "Paragraph 0",
            ElementType.PARAGRAPH
        ),

        make_element(
            1,
            "Paragraph 1",
            ElementType.PARAGRAPH
        ),

        make_element(
            2,
            "Paragraph 2",
            ElementType.PARAGRAPH
        ),
    ]

    extraction_result = ExtractionResult(
        elements=original_elements
    )

    mock_llm = MockLLMClient(
        boundaries=[999]
    )

    chunker = SemanticChunker(
        llm_client=mock_llm
    )

    result = chunker.chunk(
        extraction_result
    )

    # Invalid boundary should trigger fallback
    assert len(result) == 1

    assert result[0].elements == original_elements

    assert result[0].text == (
        "Paragraph 0\n\n"
        "Paragraph 1\n\n"
        "Paragraph 2"
    )


# =========================================================
# TEST 4
# Unsorted boundaries [5, 2]
# =========================================================

def test_unsorted_boundaries_use_fallback():

    original_elements = [
        make_element(
            0,
            "Paragraph 0",
            ElementType.PARAGRAPH
        ),

        make_element(
            2,
            "Paragraph 2",
            ElementType.PARAGRAPH
        ),

        make_element(
            5,
            "Paragraph 5",
            ElementType.PARAGRAPH
        ),
    ]

    extraction_result = ExtractionResult(
        elements=original_elements
    )

    mock_llm = MockLLMClient(
        boundaries=[5, 2]
    )

    chunker = SemanticChunker(
        llm_client=mock_llm
    )

    result = chunker.chunk(
        extraction_result
    )

    assert len(result) == 1

    assert result[0].elements == original_elements

    assert result[0].text == (
        "Paragraph 0\n\n"
        "Paragraph 2\n\n"
        "Paragraph 5"
    )


# =========================================================
# TEST 5
# Empty boundaries []
# =========================================================

def test_empty_boundaries_use_fallback():

    original_elements = [
        make_element(
            0,
            "Paragraph 0",
            ElementType.PARAGRAPH
        ),

        make_element(
            1,
            "Paragraph 1",
            ElementType.PARAGRAPH
        ),
    ]

    extraction_result = ExtractionResult(
        elements=original_elements
    )

    mock_llm = MockLLMClient(
        boundaries=[]
    )

    chunker = SemanticChunker(
        llm_client=mock_llm
    )

    result = chunker.chunk(
        extraction_result
    )

    assert len(result) == 1

    assert result[0].elements == original_elements

    assert result[0].text == (
        "Paragraph 0\n\n"
        "Paragraph 1"
    )


# =========================================================
# TEST 6
# Wrong first boundary
# =========================================================

def test_wrong_first_boundary_uses_fallback():

    original_elements = [
        make_element(
            0,
            "Paragraph 0",
            ElementType.PARAGRAPH
        ),

        make_element(
            1,
            "Paragraph 1",
            ElementType.PARAGRAPH
        ),

        make_element(
            2,
            "Paragraph 2",
            ElementType.PARAGRAPH
        ),
    ]

    extraction_result = ExtractionResult(
        elements=original_elements
    )

    mock_llm = MockLLMClient(
        boundaries=[1, 2]
    )

    chunker = SemanticChunker(
        llm_client=mock_llm
    )

    result = chunker.chunk(
        extraction_result
    )

    assert len(result) == 1

    assert result[0].elements == original_elements

    assert result[0].text == (
        "Paragraph 0\n\n"
        "Paragraph 1\n\n"
        "Paragraph 2"
    )


# =========================================================
# TEST 7
# Duplicate boundaries
# =========================================================

def test_duplicate_boundaries_use_fallback():

    original_elements = [
        make_element(
            0,
            "Paragraph 0",
            ElementType.PARAGRAPH
        ),

        make_element(
            1,
            "Paragraph 1",
            ElementType.PARAGRAPH
        ),

        make_element(
            2,
            "Paragraph 2",
            ElementType.PARAGRAPH
        ),
    ]

    extraction_result = ExtractionResult(
        elements=original_elements
    )

    mock_llm = MockLLMClient(
        boundaries=[0, 1, 1]
    )

    chunker = SemanticChunker(
        llm_client=mock_llm
    )

    result = chunker.chunk(
        extraction_result
    )

    assert len(result) == 1

    assert result[0].elements == original_elements

    assert result[0].text == (
        "Paragraph 0\n\n"
        "Paragraph 1\n\n"
        "Paragraph 2"
    )


# =========================================================
# TEST 8
# Only TABLE and CODE
# =========================================================

# =========================================================
# TEST 9
# Whitespace-only elements are ignored
# =========================================================

def test_whitespace_elements_are_ignored():

    elements = [
        make_element(
            0,
            "Paragraph 0",
            ElementType.PARAGRAPH
        ),

        make_element(
            1,
            "   ",
            ElementType.PARAGRAPH
        ),

        make_element(
            2,
            "\n\n",
            ElementType.PARAGRAPH
        ),

        make_element(
            3,
            "Paragraph 3",
            ElementType.PARAGRAPH
        ),
    ]

    extraction_result = ExtractionResult(
        elements=elements
    )

    mock_llm = MockLLMClient(
        boundaries=[0, 3]
    )

    chunker = SemanticChunker(
        llm_client=mock_llm
    )

    candidates = chunker.chunk(
        extraction_result
    )

    assert len(candidates) == 2

    assert candidates[0].text == "Paragraph 0"

    assert candidates[1].text == "Paragraph 3"


# =========================================================
# TEST 10
# Input elements are unsorted
# =========================================================

def test_elements_are_sorted_by_order_index():

    elements = [
        make_element(
            3,
            "Paragraph 3",
            ElementType.PARAGRAPH
        ),

        make_element(
            1,
            "Paragraph 1",
            ElementType.PARAGRAPH
        ),

        make_element(
            0,
            "Paragraph 0",
            ElementType.PARAGRAPH
        ),

        make_element(
            2,
            "Paragraph 2",
            ElementType.PARAGRAPH
        ),
    ]

    extraction_result = ExtractionResult(
        elements=elements
    )

    mock_llm = MockLLMClient(
        boundaries=[0, 2]
    )

    chunker = SemanticChunker(
        llm_client=mock_llm
    )

    candidates = chunker.chunk(
        extraction_result
    )

    assert len(candidates) == 2

    assert candidates[0].text == (
        "Paragraph 0\n\n"
        "Paragraph 1"
    )

    assert candidates[1].text == (
        "Paragraph 2\n\n"
        "Paragraph 3"
    )


# =========================================================
# TEST 11
# Gemini/API failure → fallback
# =========================================================

def test_gemini_failure_uses_fallback():

    original_elements = [
        make_element(
            0,
            "Paragraph 0",
            ElementType.PARAGRAPH
        ),

        make_element(
            1,
            "table content",
            ElementType.TABLE
        ),

        make_element(
            2,
            "Paragraph 2",
            ElementType.PARAGRAPH
        ),

        make_element(
            3,
            "code content",
            ElementType.CODE_BLOCK
        ),

        make_element(
            4,
            "Paragraph 4",
            ElementType.PARAGRAPH
        ),
    ]

    extraction_result = ExtractionResult(
        elements=original_elements
    )

    chunker = SemanticChunker(
        llm_client=FailingLLMClient()
    )

    result = chunker.chunk(
        extraction_result
    )

    # Gemini failed → fallback
    assert len(result) == 1

    # Original elements must be preserved
    assert result[0].elements == original_elements

    table = original_elements[1]
    code = original_elements[3]

    # Table remains
    assert table in result[0].elements

    # Code remains
    assert code in result[0].elements

    # Table/code do NOT enter narrative text
    assert table.text not in result[0].text
    assert code.text not in result[0].text

    assert result[0].text == (
        "Paragraph 0\n\n"
        "Paragraph 2\n\n"
        "Paragraph 4"
    )


# =========================================================
# TEST 12
# Multiple boundaries + TABLE/CODE between them
# =========================================================

def test_delegated_elements_follow_their_semantic_group():

    original_elements = [
        make_element(
            0,
            "RAG paragraph 0",
            ElementType.PARAGRAPH
        ),

        make_element(
            1,
            "RAG paragraph 1",
            ElementType.PARAGRAPH
        ),

        make_element(
            2,
            "RAG table",
            ElementType.TABLE
        ),

        make_element(
            3,
            "RAG paragraph 3",
            ElementType.PARAGRAPH
        ),

        make_element(
            4,
            "Authentication paragraph",
            ElementType.PARAGRAPH
        ),

        make_element(
            5,
            "Authentication code",
            ElementType.CODE_BLOCK
        ),

        make_element(
            6,
            "Authentication paragraph 6",
            ElementType.PARAGRAPH
        ),
    ]

    extraction_result = ExtractionResult(
        elements=original_elements
    )

    mock_llm = MockLLMClient(
        boundaries=[0, 4]
    )

    chunker = SemanticChunker(
        llm_client=mock_llm
    )

    result = chunker.chunk(
        extraction_result
    )

    assert len(result) == 2

    # -------------------------
    # RAG candidate
    # -------------------------

    rag_candidate = result[0]

    assert [
        element.order_index
        for element in rag_candidate.elements
    ] == [0, 1, 2, 3]

    assert rag_candidate.text == (
        "RAG paragraph 0\n\n"
        "RAG paragraph 1\n\n"
        "RAG paragraph 3"
    )

    assert original_elements[2] in rag_candidate.elements

    assert "RAG table" not in rag_candidate.text

    # -------------------------
    # Authentication candidate
    # -------------------------

    auth_candidate = result[1]

    assert [
        element.order_index
        for element in auth_candidate.elements
    ] == [4, 5, 6]

    assert auth_candidate.text == (
        "Authentication paragraph\n\n"
        "Authentication paragraph 6"
    )

    assert original_elements[5] in auth_candidate.elements

    assert "Authentication code" not in auth_candidate.text

def test_llm_failure_uses_windowed_fallback():

    elements = [
        make_element(0, "A" * 1000, ElementType.PARAGRAPH),
        make_element(1, "B" * 1000, ElementType.PARAGRAPH),
        make_element(2, "C" * 1000, ElementType.PARAGRAPH),
    ]

    mock_llm = FailingLLMClient()

    chunker = SemanticChunker(
        llm_client=mock_llm
    )

    candidates = chunker.chunk(
        ExtractionResult(elements=elements)
    )

    assert len(candidates) == 2

def test_only_delegated_elements_are_preserved():

    original_elements = [
        make_element(
            0,
            "table content",
            ElementType.TABLE
        ),

        make_element(
            1,
            "code content",
            ElementType.CODE_BLOCK
        ),
    ]

    extraction_result = ExtractionResult(
        elements=original_elements
    )

    mock_llm = MockLLMClient(
        boundaries=[0]
    )

    chunker = SemanticChunker(
        llm_client=mock_llm
    )

    result = chunker.chunk(
        extraction_result
    )

    # One preservation candidate should be created
    assert len(result) == 1

    # Original elements must be preserved
    assert result[0].elements == original_elements

    # TABLE/CODE are delegated, so they don't appear in text
    assert result[0].text == ""

    assert original_elements[0] in result[0].elements
    assert original_elements[1] in result[0].elements