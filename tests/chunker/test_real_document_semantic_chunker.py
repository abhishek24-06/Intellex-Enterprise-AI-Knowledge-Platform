from pathlib import Path
from collections import Counter

from app.dto.extraction_result import ExtractionResult
from app.enums.element_type import ElementType
from app.services.chunking.llm_chunker.semantic_chunker import SemanticChunker
from app.services.chunking.llm_chunker.gemini_client import GeminiClient


# ============================================================
# Paths
# ============================================================

TEST_DIR = Path(__file__).resolve().parent

DOCUMENT_PATH = (
    Path(__file__).resolve().parent.parent
    / "doc_test"
    / "report.docx"
)

OUTPUT_PATH = (
    TEST_DIR
    / "real_document_extracted_output.txt"
)


# ============================================================
# Real document + real Gemini integration test
# ============================================================

def test_real_document_gemini_semantic_chunking():

    # --------------------------------------------------------
    # 1. Import your existing DOCX extraction logic
    # --------------------------------------------------------
    #
    # IMPORTANT:
    # Replace this import/function with the extraction function
    # already used in your project.
    #
    # Example:
    #
    # from app.services.extraction.docx_extractor import DocxExtractor
    # extractor = DocxExtractor()
    # extraction_result = extractor.extract(DOCUMENT_PATH)
    #
    # --------------------------------------------------------

    from app.services.extraction.docx_extractor import DocxExtractor

    extractor = DocxExtractor()

    extraction_result: ExtractionResult = extractor.extract(
        DOCUMENT_PATH
    )

    # --------------------------------------------------------
    # 2. Save complete extraction output
    # --------------------------------------------------------

    with open(
        OUTPUT_PATH,
        "w",
        encoding="utf-8"
    ) as file:

        file.write("=" * 80 + "\n")
        file.write("REAL DOCUMENT EXTRACTION\n")
        file.write("=" * 80 + "\n\n")

        file.write(
            f"Document: {DOCUMENT_PATH}\n"
        )

        file.write(
            f"Total extracted elements: "
            f"{len(extraction_result.elements)}\n\n"
        )

        for element in extraction_result.elements:

            file.write(
                f"order={element.order_index} | "
                f"type={element.element_type} | "
                f"text={element.text!r}\n"
            )

        # ----------------------------------------------------
        # 3. Run real Gemini semantic chunking
        # ----------------------------------------------------

        gemini_client = GeminiClient()

        chunker = SemanticChunker(
            llm_client=gemini_client
        )

        candidates = chunker.chunk(
            extraction_result
        )

        file.write("\n\n")
        file.write("=" * 80 + "\n")
        file.write("REAL GEMINI SEMANTIC CHUNKING RESULT\n")
        file.write("=" * 80 + "\n\n")

        file.write(
            f"Number of candidates: "
            f"{len(candidates)}\n\n"
        )

        # ----------------------------------------------------
        # 4. Write every candidate
        # ----------------------------------------------------

        for i, candidate in enumerate(candidates):

            file.write("-" * 80 + "\n")
            file.write(
                f"CANDIDATE {i}\n"
            )
            file.write("-" * 80 + "\n\n")

            file.write("TEXT:\n\n")

            file.write(
                candidate.text
            )

            file.write("\n\nELEMENTS:\n")

            for element in candidate.elements:

                file.write(
                    f"  order_index={element.order_index} | "
                    f"type={element.element_type} | "
                    f"text={element.text!r}\n"
                )

            file.write("\n")

        # ----------------------------------------------------
        # 5. Validation section
        # ----------------------------------------------------

        file.write("\n")
        file.write("=" * 80 + "\n")
        file.write("INTEGRATION VALIDATION\n")
        file.write("=" * 80 + "\n\n")

        # ----------------------------------------------------
        # Original element IDs
        # ----------------------------------------------------

        original_ids = {
            element.order_index
            for element in extraction_result.elements
        }

        # ----------------------------------------------------
        # IDs appearing inside candidates
        # ----------------------------------------------------

        chunked_ids = [
            element.order_index
            for candidate in candidates
            for element in candidate.elements
        ]

        chunked_id_set = set(chunked_ids)

        # ----------------------------------------------------
        # Validation 1: No content loss
        # ----------------------------------------------------

        no_content_loss = (
            original_ids == chunked_id_set
        )

        file.write(
            f"1. No content loss: "
            f"{'PASS' if no_content_loss else 'FAIL'}\n"
        )

        file.write(
            f"   Original elements: "
            f"{len(original_ids)}\n"
        )

        file.write(
            f"   Chunked elements: "
            f"{len(chunked_id_set)}\n\n"
        )

        assert original_ids == chunked_id_set, (
            "Some original elements were lost "
            "during semantic chunking."
        )

        # ----------------------------------------------------
        # Validation 2: No duplication
        # ----------------------------------------------------

        counts = Counter(
            chunked_ids
        )

        duplicated_ids = [
            order_index
            for order_index, count in counts.items()
            if count != 1
        ]

        no_duplication = (
            len(duplicated_ids) == 0
        )

        file.write(
            f"2. No duplication: "
            f"{'PASS' if no_duplication else 'FAIL'}\n"
        )

        if duplicated_ids:
            file.write(
                f"   Duplicated IDs: "
                f"{duplicated_ids}\n"
            )

        file.write("\n")

        assert not duplicated_ids, (
            f"Elements were duplicated: "
            f"{duplicated_ids}"
        )

        # ----------------------------------------------------
        # Validation 3: Element ordering
        # ----------------------------------------------------

        all_candidates_ordered = True

        for i, candidate in enumerate(candidates):

            orders = [
                element.order_index
                for element in candidate.elements
            ]

            if orders != sorted(orders):

                all_candidates_ordered = False

                file.write(
                    f"   Candidate {i} is NOT ordered: "
                    f"{orders}\n"
                )

        file.write(
            f"3. Element order preserved: "
            f"{'PASS' if all_candidates_ordered else 'FAIL'}\n\n"
        )

        assert all_candidates_ordered, (
            "Elements inside a candidate are "
            "not in original document order."
        )

        # ----------------------------------------------------
        # Validation 4: Delegated elements preserved
        # ----------------------------------------------------

        original_delegated = {
            element.order_index
            for element in extraction_result.elements
            if element.element_type
            in {
                ElementType.TABLE,
                ElementType.CODE_BLOCK,
            }
        }

        chunked_delegated = {
            element.order_index
            for candidate in candidates
            for element in candidate.elements
            if element.element_type
            in {
                ElementType.TABLE,
                ElementType.CODE_BLOCK,
            }
        }

        delegated_preserved = (
            original_delegated == chunked_delegated
        )

        file.write(
            f"4. Tables/code preserved: "
            f"{'PASS' if delegated_preserved else 'FAIL'}\n"
        )

        file.write(
            f"   Original delegated elements: "
            f"{len(original_delegated)}\n"
        )

        file.write(
            f"   Chunked delegated elements: "
            f"{len(chunked_delegated)}\n\n"
        )

        assert original_delegated == chunked_delegated, (
            "Table/code elements were lost."
        )

        # ----------------------------------------------------
        # Validation 5: Delegated content not duplicated
        # into candidate.text
        # ----------------------------------------------------

        delegated_text_leaks = []

        for candidate_index, candidate in enumerate(candidates):

            for element in candidate.elements:

                if element.element_type not in {
                    ElementType.TABLE,
                    ElementType.CODE_BLOCK,
                }:
                    continue

                if not element.text.strip():
                    continue

                if element.text.strip() in candidate.text:
                    delegated_text_leaks.append(
                        (
                            candidate_index,
                            element.order_index
                        )
                    )

        no_delegated_text_leak = (
            len(delegated_text_leaks) == 0
        )

        file.write(
            f"5. Delegated content excluded from text: "
            f"{'PASS' if no_delegated_text_leak else 'FAIL'}\n"
        )

        if delegated_text_leaks:

            file.write(
                f"   Leaks: "
                f"{delegated_text_leaks}\n"
            )

        file.write("\n")

        assert not delegated_text_leaks, (
            "Table/code content was incorrectly "
            "included inside candidate.text."
        )

        # ----------------------------------------------------
        # Final result
        # ----------------------------------------------------

        file.write("=" * 80 + "\n")
        file.write("ALL VALIDATION CHECKS PASSED\n")
        file.write("=" * 80 + "\n")

    # --------------------------------------------------------
    # Also show a small result in pytest terminal
    # --------------------------------------------------------

    print("\n")
    print("=" * 70)
    print("REAL DOCUMENT SEMANTIC CHUNKING")
    print("=" * 70)

    print(
        f"Extracted elements: "
        f"{len(extraction_result.elements)}"
    )

    print(
        f"Semantic candidates: "
        f"{len(candidates)}"
    )

    print(
        f"Output saved to:\n"
        f"{OUTPUT_PATH}"
    )

    print("\nValidation:")
    print("  ✓ No content loss")
    print("  ✓ No duplication")
    print("  ✓ Element order preserved")
    print("  ✓ Tables/code preserved")
    print("  ✓ Tables/code excluded from candidate.text")