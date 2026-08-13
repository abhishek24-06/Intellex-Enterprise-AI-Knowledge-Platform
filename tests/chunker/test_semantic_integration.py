from collections import Counter

from app.dto.extracted_element import ExtractedElement
from app.dto.extraction_result import ExtractionResult
from app.enums.element_type import ElementType
from app.services.chunking.llm_chunker.gemini_client import GeminiClient
from app.services.chunking.llm_chunker.semantic_chunker import SemanticChunker


# =========================================================
# TEST DATA
# =========================================================

def create_test_extraction_result() -> ExtractionResult:
    """
    Creates a small realistic unstructured document.

    The document contains:
        - narrative paragraphs
        - a table
        - a code block
        - two different semantic topics
    """

    elements = [

        # =================================================
        # TOPIC 1: RAG
        # =================================================

        ExtractedElement(
            order_index=0,
            text=(
                "Intellex uses retrieval augmented generation "
                "to answer questions from enterprise documents."
            ),
            element_type=ElementType.PARAGRAPH,
        ),

        ExtractedElement(
            order_index=1,
            text=(
                "The retrieval system first searches the "
                "knowledge base for relevant information."
            ),
            element_type=ElementType.PARAGRAPH,
        ),

        ExtractedElement(
            order_index=2,
            text=(
                "The retrieved documents are then provided "
                "to the language model as context."
            ),
            element_type=ElementType.PARAGRAPH,
        ),

        # TABLE belongs to the RAG section.
        # Gemini does NOT see this element.
        # Python should attach it back to the correct group.
        ExtractedElement(
            order_index=3,
            text=(
                "Component | Responsibility\n"
                "Retriever | Finds relevant documents\n"
                "Generator | Generates the final answer"
            ),
            element_type=ElementType.TABLE,
        ),

        # =================================================
        # TOPIC 2: AUTHENTICATION
        # =================================================

        ExtractedElement(
            order_index=4,
            text=(
                "Intellex uses JWT authentication "
                "to protect its API endpoints."
            ),
            element_type=ElementType.PARAGRAPH,
        ),

        ExtractedElement(
            order_index=5,
            text=(
                "Users must provide a valid access token "
                "when accessing protected resources."
            ),
            element_type=ElementType.PARAGRAPH,
        ),

        # CODE belongs to the authentication section.
        ExtractedElement(
            order_index=6,
            text="Authorization: Bearer <token>",
            element_type=ElementType.CODE_BLOCK,
        ),

        ExtractedElement(
            order_index=7,
            text=(
                "The authentication layer also ensures "
                "that users can only access their authorized "
                "knowledge bases."
            ),
            element_type=ElementType.PARAGRAPH,
        ),
    ]

    return ExtractionResult(
        elements=elements
    )


# =========================================================
# TEST 1
# REAL GEMINI INTEGRATION TEST
# =========================================================

def test_real_gemini_semantic_chunking():

    extraction_result = create_test_extraction_result()

    # This uses your REAL Gemini API.
    chunker = SemanticChunker(
        llm_client=GeminiClient()
    )

    candidates = chunker.chunk(
        extraction_result
    )

    # -----------------------------------------------------
    # 1. We should get at least one candidate
    # -----------------------------------------------------

    assert candidates

    # -----------------------------------------------------
    # Print candidates for manual inspection
    # -----------------------------------------------------

    print("\n")
    print("=" * 70)
    print("REAL GEMINI SEMANTIC CHUNKING RESULT")
    print("=" * 70)

    for i, candidate in enumerate(candidates):

        print("\n")
        print("-" * 70)
        print(f"CANDIDATE {i}")
        print("-" * 70)

        print("\nTEXT:")
        print(candidate.text)

        print("\nELEMENTS:")

        for element in candidate.elements:

            print(
                f"  order_index={element.order_index} | "
                f"type={element.element_type} | "
                f"text={repr(element.text[:100])}"
            )

    # -----------------------------------------------------
    # 2. NO CONTENT LOSS
    # -----------------------------------------------------

    original_ids = {
        element.order_index
        for element in extraction_result.elements
    }

    chunked_ids = {
        element.order_index
        for candidate in candidates
        for element in candidate.elements
    }

    assert original_ids == chunked_ids

    # -----------------------------------------------------
    # 3. NO DUPLICATION
    # -----------------------------------------------------

    counts = Counter(
        element.order_index
        for candidate in candidates
        for element in candidate.elements
    )

    assert all(
        count == 1
        for count in counts.values()
    )

    # -----------------------------------------------------
    # 4. ORDER IS PRESERVED
    # -----------------------------------------------------

    for candidate in candidates:

        orders = [
            element.order_index
            for element in candidate.elements
        ]

        assert orders == sorted(orders)

    # -----------------------------------------------------
    # 5. TABLE/CODE ARE PRESERVED
    #    BUT NOT INCLUDED IN candidate.text
    # -----------------------------------------------------

    delegated_elements = [
        element
        for element in extraction_result.elements
        if element.element_type in {
            ElementType.TABLE,
            ElementType.CODE_BLOCK,
        }
    ]

    for delegated in delegated_elements:

        # It must appear in exactly one candidate.
        matching_candidates = [
            candidate
            for candidate in candidates
            if delegated in candidate.elements
        ]

        assert len(matching_candidates) == 1

        # Its raw content must not be inside narrative text.
        for candidate in matching_candidates:

            assert delegated.text not in candidate.text


# =========================================================
# FAILING LLM
# =========================================================

class FailingLLMClient:

    def detect_boundaries(self, prompt):

        raise RuntimeError(
            "Gemini unavailable"
        )


# =========================================================
# TEST 2
# GEMINI FAILURE → WINDOWED FALLBACK
# =========================================================

def test_gemini_failure_uses_windowed_fallback():

    extraction_result = create_test_extraction_result()

    # We intentionally DON'T use Gemini here.
    chunker = SemanticChunker(
        llm_client=FailingLLMClient()
    )

    candidates = chunker.chunk(
        extraction_result
    )

    # -----------------------------------------------------
    # 1. Fallback should still produce candidates
    # -----------------------------------------------------

    assert candidates

    print("\n")
    print("=" * 70)
    print("FALLBACK CHUNKING RESULT")
    print("=" * 70)

    for i, candidate in enumerate(candidates):

        print("\n")
        print("-" * 70)
        print(f"FALLBACK CANDIDATE {i}")
        print("-" * 70)

        print("\nTEXT:")
        print(candidate.text)

        print("\nELEMENTS:")

        for element in candidate.elements:

            print(
                f"  order_index={element.order_index} | "
                f"type={element.element_type} | "
                f"text={repr(element.text[:100])}"
            )

    # -----------------------------------------------------
    # 2. NO CONTENT LOSS
    # -----------------------------------------------------

    original_ids = {
        element.order_index
        for element in extraction_result.elements
    }

    chunked_ids = {
        element.order_index
        for candidate in candidates
        for element in candidate.elements
    }

    assert original_ids == chunked_ids

    # -----------------------------------------------------
    # 3. NO DUPLICATION
    # -----------------------------------------------------

    counts = Counter(
        element.order_index
        for candidate in candidates
        for element in candidate.elements
    )

    assert all(
        count == 1
        for count in counts.values()
    )

    # -----------------------------------------------------
    # 4. ORDER IS PRESERVED
    # -----------------------------------------------------

    for candidate in candidates:

        orders = [
            element.order_index
            for element in candidate.elements
        ]

        assert orders == sorted(orders)

    # -----------------------------------------------------
    # 5. TABLE/CODE ARE PRESERVED
    # -----------------------------------------------------

    delegated_elements = [
        element
        for element in extraction_result.elements
        if element.element_type in {
            ElementType.TABLE,
            ElementType.CODE_BLOCK,
        }
    ]

    for delegated in delegated_elements:

        matching_candidates = [
            candidate
            for candidate in candidates
            if delegated in candidate.elements
        ]

        assert len(matching_candidates) == 1

        for candidate in matching_candidates:

            assert delegated.text not in candidate.text