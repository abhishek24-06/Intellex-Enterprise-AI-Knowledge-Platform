from pathlib import Path

from app.services.extraction.txt_extractor import TxtExtractor

from app.services.chunking.structure_detection.detector import (
    StructureDetector,
)

from app.services.chunking.structure_builder.structure_builder import (
    DocumentStructureBuilder,
)

from app.services.chunking.hierarchy.hierarchy_chunker import (
    HierarchyChunker,
)

from app.services.chunking.llm_chunker.semantic_chunker import (
    SemanticChunker,
)

from app.services.chunking.llm_chunker.gemini_client import (
    GeminiClient,
)

from app.services.chunking.routing.element_router import (
    ElementRouter,
)

from app.services.chunking.recursive_splitter.narrative_safety_splitter import (
    NarrativeSafetySplitter,
)

from app.services.chunking.table.table_chunker import (
    TableChunker,
)

from app.services.chunking.code.code_chunker import (
    CodeChunker,
)

from app.services.chunking.final_chunker_validator.validator import (
    FinalChunkValidator,
)

from app.services.pipeline.document_chunker_pipeline import (
    DocumentChunker,
)

from app.enums.chunk_type import ChunkType
from app.enums.element_type import ElementType


def test_real_txt_full_pipeline():

    # ============================================================
    # 1. LOCATE REAL TXT FILE
    # ============================================================

    txt_path = Path(
        "tests/txt_test/sample.txt"
    )

    assert txt_path.exists(), (
        f"Test TXT file not found: {txt_path}"
    )

    # ============================================================
    # 2. REAL TXT EXTRACTION
    # ============================================================

    extractor = TxtExtractor()

    extraction_result = extractor.extract(
        str(txt_path)
    )

    # ============================================================
    # 3. EXTRACTION SANITY CHECKS
    # ============================================================

    assert extraction_result is not None

    assert extraction_result.elements, (
        "TXT extractor returned no elements."
    )

    # ------------------------------------------------------------
    # Every element must have a valid order index
    # ------------------------------------------------------------

    order_indexes = [
        element.order_index
        for element in extraction_result.elements
    ]

    assert all(
        order_index >= 0
        for order_index in order_indexes
    )

    # Order indexes should be unique.
    assert len(order_indexes) == len(
        set(order_indexes)
    )

    # ------------------------------------------------------------
    # TXT provenance
    #
    # Do not assume a metadata schema that the current extractor
    # does not provide. The existing TXT extractor test only
    # establishes that extraction succeeds and exposes metadata.
    # ------------------------------------------------------------

    print("\n" + "=" * 80)
    print("TXT EXTRACTION")
    print("=" * 80)

    print(
        f"Extracted elements: "
        f"{len(extraction_result.elements)}"
    )

    # ============================================================
    # 4. VERIFY TXT ELEMENT TYPES
    # ============================================================

    element_types = {
        element.element_type
        for element in extraction_result.elements
    }

    print(
        f"Element types: "
        f"{sorted(str(element_type) for element_type in element_types)}"
    )

    # TXT is expected to primarily produce narrative content.
    #
    # We deliberately do NOT require a specific set of element
    # types here because TXT has no Markdown/DOCX structural
    # syntax that should be assumed by this E2E test.
    #
    # The important invariant is that extracted elements actually
    # reach the final pipeline.

    assert all(
        element.element_type is not None
        for element in extraction_result.elements
    )

    # ============================================================
    # 5. BUILD REAL CHUNKING PIPELINE
    # ============================================================

    structure_detector = StructureDetector()

    structure_builder = DocumentStructureBuilder()

    hierarchy_chunker = HierarchyChunker()

    gemini_client = GeminiClient()

    semantic_chunker = SemanticChunker(
        llm_client=gemini_client,
    )

    element_router = ElementRouter()

    narrative_safety_splitter = (
        NarrativeSafetySplitter()
    )

    table_chunker = TableChunker()

    code_chunker = CodeChunker()

    validator = FinalChunkValidator()

    document_chunker = DocumentChunker(
        structure_detector=structure_detector,
        structure_builder=structure_builder,
        hierarchy_chunker=hierarchy_chunker,
        semantic_chunker=semantic_chunker,
        element_router=element_router,
        narrative_safety_splitter=narrative_safety_splitter,
        table_chunker=table_chunker,
        code_chunker=code_chunker,
        final_chunk_validator=validator,
    )

    # ============================================================
    # 6. EXTRACTION RESULT → DOCUMENT CHUNKER
    # ============================================================

    final_chunks = document_chunker.chunk(
        extraction_result
    )

    # ============================================================
    # 7. BASIC FINAL CHUNK SANITY CHECKS
    # ============================================================

    assert final_chunks, (
        "DocumentChunker returned no final chunks."
    )

    assert all(
        chunk.text.strip()
        for chunk in final_chunks
    ), (
        "A final chunk contains empty text."
    )

    assert all(
        chunk.elements
        for chunk in final_chunks
    ), (
        "A final chunk contains no source elements."
    )

    # ============================================================
    # 8. FINAL CHUNKS MUST BE ORDERED
    # ============================================================

    chunk_order_indexes = [
        chunk.order_index
        for chunk in final_chunks
    ]

    assert chunk_order_indexes == sorted(
        chunk_order_indexes
    ), (
        "Final chunks are not ordered by order_index."
    )

    # ============================================================
    # 9. EVERY FINAL CHUNK MUST HAVE VALID TYPE
    # ============================================================

    valid_types = {
        ChunkType.NARRATIVE,
        ChunkType.TABLE,
        ChunkType.CODE,
    }

    assert all(
        chunk.chunk_type in valid_types
        for chunk in final_chunks
    ), (
        "A final chunk has an invalid chunk_type."
    )

    # ============================================================
    # 10. EVERY FINAL CHUNK MUST REFERENCE A REAL
    #     SOURCE ELEMENT
    # ============================================================

    source_order_indexes = {
        element.order_index
        for element in extraction_result.elements
    }

    for chunk in final_chunks:

        for element in chunk.elements:

            assert (
                element.order_index
                in source_order_indexes
            ), (
                "Final chunk references an element that "
                "does not exist in ExtractionResult."
            )

    # ============================================================
    # 11. CHUNK ORDER MUST MATCH FIRST SOURCE ELEMENT
    # ============================================================

    for chunk in final_chunks:

        minimum_source_order = min(
            element.order_index
            for element in chunk.elements
        )

        assert (
            chunk.order_index
            == minimum_source_order
        ), (
            "FinalChunk.order_index does not match "
            "the first source element position."
        )

    # ============================================================
    # 12. METADATA MUST BE A DICT
    # ============================================================

    for chunk in final_chunks:

        assert isinstance(
            chunk.metadata,
            dict,
        ), (
            "FinalChunk.metadata must be a dictionary."
        )

    # ============================================================
    # 13. SOURCE COVERAGE
    # ============================================================
    #
    # TXT does not have Markdown-style structural headings that
    # are intentionally consumed as hierarchy-only elements.
    #
    # Therefore every extracted TXT element should be represented
    # by at least one final chunk.
    #
    # If this fails, print the exact missing elements before the
    # assertion so we can distinguish:
    #
    #   - actual content loss
    #   - unexpected extractor behavior
    #   - an incorrect assumption in this test
    #

    covered_order_indexes = {
        element.order_index
        for chunk in final_chunks
        for element in chunk.elements
    }

    missing_elements = (
        source_order_indexes
        - covered_order_indexes
    )

    if missing_elements:

        print("\n" + "=" * 80)
        print("MISSING TXT SOURCE ELEMENTS")
        print("=" * 80)

        print(
            f"\nMissing count: "
            f"{len(missing_elements)}"
        )

        print(
            f"Missing order indexes: "
            f"{sorted(missing_elements)}"
        )

        print("\n" + "-" * 80)

        for element in extraction_result.elements:

            if element.order_index not in missing_elements:
                continue

            print(
                f"\norder_index : "
                f"{element.order_index}"
            )

            print(
                f"element_type: "
                f"{element.element_type}"
            )

            print(
                f"text        : "
                f"{element.text!r}"
            )

            print(
                f"metadata    : "
                f"{element.metadata}"
            )

        print("\n" + "-" * 80)
        print("FINAL CHUNK COVERAGE")
        print("-" * 80)

        for chunk in final_chunks:

            chunk_element_indexes = [
                element.order_index
                for element in chunk.elements
            ]

            print(
                f"\nchunk_type="
                f"{chunk.chunk_type}"
            )

            print(
                f"order_index="
                f"{chunk.order_index}"
            )

            print(
                f"source_elements="
                f"{chunk_element_indexes}"
            )

            print(
                f"text="
                f"{chunk.text!r}"
            )

        print("\n" + "=" * 80)

    assert missing_elements == set(), (
        "Source elements were lost during the full "
        "TXT pipeline: "
        f"{sorted(missing_elements)}"
    )

    # ============================================================
    # 14. EXPLICIT FINAL VALIDATOR RUN
    # ============================================================

    validator.validate(
        chunks=final_chunks,
        source_elements=extraction_result.elements,
    )

    # ============================================================
    # 15. FINAL CHUNK DISTRIBUTION
    # ============================================================

    chunk_type_counts = {
        chunk_type: sum(
            chunk.chunk_type == chunk_type
            for chunk in final_chunks
        )
        for chunk_type in valid_types
    }

    print("\n" + "=" * 80)
    print("FINAL CHUNK DISTRIBUTION")
    print("=" * 80)

    for chunk_type, count in chunk_type_counts.items():

        print(
            f"  {chunk_type.value}: "
            f"{count}"
        )

    # ============================================================
    # 16. EXTRACTED ELEMENT DISTRIBUTION
    # ============================================================

    element_type_counts = {}

    for element in extraction_result.elements:

        element_type = element.element_type

        element_type_counts[element_type] = (
            element_type_counts.get(
                element_type,
                0,
            )
            + 1
        )

    print("\n" + "=" * 80)
    print("EXTRACTED ELEMENT DISTRIBUTION")
    print("=" * 80)

    for element_type, count in element_type_counts.items():

        print(
            f"  {element_type}: "
            f"{count}"
        )

    # ============================================================
    # 17. FINAL SUMMARY
    # ============================================================

    print("\n" + "=" * 80)
    print("TXT FULL PIPELINE TEST PASSED")
    print("=" * 80)

    print(
        f"Source elements : "
        f"{len(extraction_result.elements)}"
    )

    print(
        f"Final chunks    : "
        f"{len(final_chunks)}"
    )

    print(
        f"Narrative chunks: "
        f"{chunk_type_counts[ChunkType.NARRATIVE]}"
    )

    print(
        f"Table chunks    : "
        f"{chunk_type_counts[ChunkType.TABLE]}"
    )

    print(
        f"Code chunks     : "
        f"{chunk_type_counts[ChunkType.CODE]}"
    )

    print("=" * 80)