import os
from pathlib import Path

os.environ["TORCH_COMPILE_DISABLE"] = "1"

from app.services.extraction.pdf.pdf_extractor import PdfExtractor

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
from app.services.chunking.final_chunker.document_chunker import (
    DocumentChunker,
)

from app.enums.chunk_type import ChunkType
from app.enums.element_type import ElementType


def test_real_pdf_full_pipeline():

    # ============================================================
    # 1. LOCATE REAL PDF
    # ============================================================

    test_dir = Path(__file__).parent

    pdf_path = test_dir / "report.pdf"

    assert pdf_path.exists(), (
        f"Test PDF not found: {pdf_path}"
    )

    # ============================================================
    # 2. REAL PDF EXTRACTION
    # ============================================================

    extractor = PdfExtractor()

    extraction_result = extractor.extract(
        pdf_path,
        document_id="e2e-pdf-test",
        filename=pdf_path.name,
    )

    # ------------------------------------------------------------
    # Extraction sanity checks
    # ------------------------------------------------------------

    assert extraction_result is not None
    assert extraction_result.elements

    order_indexes = [
        element.order_index
        for element in extraction_result.elements
    ]

    # Every element has an order index
    assert all(
        order_index >= 0
        for order_index in order_indexes
    )

    # Order indexes are unique
    assert len(order_indexes) == len(set(order_indexes))

    # PDF provenance
    assert all(
        element.metadata.get("source") == "docling"
        for element in extraction_result.elements
    )

    assert all(
        element.metadata.get("filename") == pdf_path.name
        for element in extraction_result.elements
    )

    # ============================================================
    # 3. CHECK ELEMENT TYPES EXIST
    # ============================================================

    element_types = {
        element.element_type
        for element in extraction_result.elements
    }

    assert ElementType.PARAGRAPH in element_types

    # These are expected in our real test PDF
    assert ElementType.TABLE in element_types
    assert ElementType.CODE_BLOCK in element_types

    # ============================================================
    # 4. BUILD CHUNKING PIPELINE
    # ============================================================

    structure_detector = StructureDetector()

    structure_builder = DocumentStructureBuilder()

    hierarchy_chunker = HierarchyChunker()

    gemini_client = GeminiClient()

    semantic_chunker = SemanticChunker(
        llm_client=gemini_client,
    )

    element_router = ElementRouter()

    narrative_safety_splitter = NarrativeSafetySplitter()

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
    # 5. INTERMEDIATE COVERAGE DIAGNOSTIC
    #
    # Do NOT call document_chunker.chunk() yet.
    #
    # We want to determine exactly where source elements disappear:
    #
    # ExtractionResult
    #       ↓
    # Candidates
    #       ↓
    # RoutedChunks
    #       ↓
    # FinalChunks
    #
    # IMPORTANT:
    # HEADING elements are structural information.
    # They may be consumed into:
    #
    #   candidate.heading
    #   candidate.section_path
    #
    # and therefore do NOT have to appear inside
    # candidate.elements.
    #
    # All non-heading/content elements MUST be represented
    # by at least one candidate.
    # ============================================================
    
    detection = structure_detector.detect(
        extraction_result
    )
    
    print()
    print("=" * 80)
    print("PDF PIPELINE COVERAGE DIAGNOSTIC")
    print("=" * 80)
    
    print(
        "\nSTRUCTURE TYPE:",
        detection.structure_type,
    )
    
    # ------------------------------------------------------------
    # Source element indexes
    # ------------------------------------------------------------
    
    source_indexes = {
        element.order_index
        for element in extraction_result.elements
    }
    
    print(
        "\nSOURCE ELEMENT COUNT:",
        len(source_indexes),
    )
    
    # ------------------------------------------------------------
    # Separate structural headings from content elements
    # ------------------------------------------------------------
    
    heading_indexes = {
        element.order_index
        for element in extraction_result.elements
        if element.element_type == ElementType.HEADING
    }
    
    content_indexes = (
        source_indexes - heading_indexes
    )
    
    print(
        "\nSTRUCTURAL HEADING COUNT:",
        len(heading_indexes),
    )
    
    print(
        "CONTENT ELEMENT COUNT:",
        len(content_indexes),
    )
    
    # ------------------------------------------------------------
    # Candidate stage
    # ------------------------------------------------------------
    
    candidates = document_chunker._build_candidates(
        extraction_result=extraction_result,
        structure_type=detection.structure_type,
    )
    
    candidate_indexes = {
        element.order_index
        for candidate in candidates
        for element in candidate.elements
    }
    
    print(
        "\nCANDIDATE COUNT:",
        len(candidates),
    )
    
    print(
        "ELEMENTS REPRESENTED BY CANDIDATES:",
        len(candidate_indexes),
    )
    
    # ------------------------------------------------------------
    # Candidate coverage
    # ------------------------------------------------------------
    
    represented_content_indexes = (
        candidate_indexes & content_indexes
    )
    
    missing_content_indexes = (
        content_indexes - candidate_indexes
    )
    
    missing_heading_indexes = (
        heading_indexes - candidate_indexes
    )
    
    print(
        "\nCONTENT ELEMENTS REPRESENTED BY CANDIDATES:",
        len(represented_content_indexes),
    )
    
    print(
        "MISSING CONTENT ELEMENTS:",
        sorted(missing_content_indexes),
    )
    
    print(
        "\nHEADINGS USED AS STRUCTURAL INFORMATION:",
        len(missing_heading_indexes),
    )
    
    print(
        "MISSING HEADING INDEXES:",
        sorted(missing_heading_indexes),
    )
    
    # ------------------------------------------------------------
    # Candidate details
    # ------------------------------------------------------------
    
    print("\nCANDIDATE DETAILS:")
    
    for index, candidate in enumerate(candidates):
    
        candidate_indexes_for_this_candidate = [
            element.order_index
            for element in candidate.elements
        ]
    
        print(
            f"\n  Candidate {index}:"
        )
    
        print(
            "    order_indexes:",
            candidate_indexes_for_this_candidate,
        )
    
        print(
            "    heading:",
            candidate.heading,
        )
    
        print(
            "    section_path:",
            candidate.section_path,
        )
    
        print(
            "    text_chars:",
            len(candidate.text or ""),
        )
    
    # ------------------------------------------------------------
    # Stop if actual CONTENT elements disappear
    #
    # Headings are intentionally allowed to disappear from
    # candidate.elements because they can be represented through
    # candidate.heading / section_path.
    # ------------------------------------------------------------
    
    if missing_content_indexes:
    
        missing_elements = [
            element
            for element in extraction_result.elements
            if element.order_index in missing_content_indexes
        ]
    
        print("\nMISSING CONTENT ELEMENT DETAILS:")
    
        for element in missing_elements:
    
            print(
                f"\n  order_index={element.order_index}"
            )
    
            print(
                f"  type={element.element_type}"
            )
    
            print(
                f"  text={element.text[:200]!r}"
            )
    
            print(
                f"  metadata={element.metadata}"
            )
    
    assert not missing_content_indexes, (
        "Non-heading source elements were lost while building "
        "ChunkCandidate objects. "
        f"Missing order_index values: "
        f"{sorted(missing_content_indexes)}"
    )
    
    # ------------------------------------------------------------
    # Verify that every heading is still represented structurally
    #
    # A heading does not need to be inside candidate.elements,
    # but it should normally be represented as either:
    #
    #   candidate.heading
    #   candidate.section_path
    #
    # This is diagnostic rather than a strict coverage assertion
    # because different structure builders may legitimately handle
    # headings differently.
    # ------------------------------------------------------------
    
    structurally_represented_heading_indexes = set()
    
    for candidate in candidates:
    
        candidate_heading = candidate.heading
    
        candidate_section_path = (
            candidate.section_path or []
        )
    
        for element in extraction_result.elements:
    
            if element.order_index not in heading_indexes:
                continue
    
            heading_text = (element.text or "").strip()
    
            if not heading_text:
                continue
    
            if candidate_heading:
                if heading_text == str(candidate_heading).strip():
                    structurally_represented_heading_indexes.add(
                        element.order_index
                    )
                    continue
    
            for section in candidate_section_path:
    
                if heading_text == str(section).strip():
    
                    structurally_represented_heading_indexes.add(
                        element.order_index
                    )
    
                    break
    
    print(
        "\nHEADINGS REPRESENTED STRUCTURALLY:",
        len(structurally_represented_heading_indexes),
    )
    
    print(
        "HEADINGS NOT REPRESENTED STRUCTURALLY:",
        sorted(
            heading_indexes
            - structurally_represented_heading_indexes
        ),
    )
    
    print()
    print("=" * 80)
    print("CANDIDATE COVERAGE CHECK PASSED")
    print("=" * 80)
     # ============================================================
    # 6. ROUTING COVERAGE
    # ============================================================
    
    routed_chunks = []
    
    for candidate in candidates:
    
        routed_chunks.extend(
            element_router.route(candidate)
        )
    
    routed_indexes = {
        element.order_index
        for routed_chunk in routed_chunks
        for element in routed_chunk.elements
    }
    
    # ------------------------------------------------------------
    # Only CONTENT elements must survive routing.
    #
    # Heading elements are structural metadata represented through
    # candidate.heading / section_path and therefore do not have to
    # appear inside RoutedChunk.elements.
    # ------------------------------------------------------------
    
    missing_after_routing = (
        content_indexes - routed_indexes
    )
    
    print(
        "\nROUTED CHUNK COUNT:",
        len(routed_chunks),
    )
    
    print(
        "ELEMENTS REPRESENTED BY ROUTED CHUNKS:",
        len(routed_indexes),
    )
    
    print(
        "MISSING CONTENT AFTER ROUTING:",
        sorted(missing_after_routing),
    )
    
    # ------------------------------------------------------------
    # Routed chunk details
    # ------------------------------------------------------------
    
    print("\nROUTED CHUNK DETAILS:")
    
    for index, routed_chunk in enumerate(
        routed_chunks
    ):
    
        routed_indexes_for_this_chunk = [
            element.order_index
            for element in routed_chunk.elements
        ]
    
        print(
            f"\n  RoutedChunk {index}:"
        )
    
        print(
            "    type:",
            routed_chunk.chunk_type,
        )
    
        print(
            "    order_index:",
            routed_chunk.order_index,
        )
    
        print(
            "    element_indexes:",
            routed_indexes_for_this_chunk,
        )
    
        print(
            "    section_path:",
            routed_chunk.section_path,
        )
    
    assert not missing_after_routing, (
        "Non-heading source elements were lost during "
        "ElementRouter routing. "
        f"Missing order_index values: "
        f"{sorted(missing_after_routing)}"
    )
    
    print()
    print("=" * 80)
    print("ROUTING COVERAGE CHECK PASSED")
    print("=" * 80)

    # ============================================================
    # 7. RUN THE REAL DOCUMENT CHUNKER
    # ============================================================

    final_chunks = document_chunker.chunk(
        extraction_result
    )

    # ============================================================
    # 8. BASIC FINAL OUTPUT VALIDATION
    # ============================================================

    assert final_chunks

    # Every final chunk must contain text
    assert all(
        chunk.text is not None
        and chunk.text.strip()
        for chunk in final_chunks
    )

    # Every final chunk must contain source elements
    assert all(
        chunk.elements
        for chunk in final_chunks
    )

    # ============================================================
    # 9. FINAL CHUNK ORDER
    # ============================================================

    chunk_order_indexes = [
        chunk.order_index
        for chunk in final_chunks
    ]

    assert chunk_order_indexes == sorted(
        chunk_order_indexes
    )

    # ============================================================
    # 10. VALID CHUNK TYPES
    # ============================================================

    valid_types = {
        ChunkType.NARRATIVE,
        ChunkType.TABLE,
        ChunkType.CODE,
    }

    assert all(
        chunk.chunk_type in valid_types
        for chunk in final_chunks
    )

    # ============================================================
    # 11. EVERY FINAL CHUNK REFERENCES A REAL SOURCE ELEMENT
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
            )

    # ============================================================
    # 12. FINAL CHUNK ORDER_INDEX MUST MATCH SOURCE
    # ============================================================

    for chunk in final_chunks:

        minimum_source_order = min(
            element.order_index
            for element in chunk.elements
        )

        assert (
            chunk.order_index
            == minimum_source_order
        )

    # ============================================================
    # 13. FINAL CHUNK TYPE DISTRIBUTION
    # ============================================================

    chunk_type_counts = {}

    for chunk in final_chunks:

        chunk_type = chunk.chunk_type

        chunk_type_counts[chunk_type] = (
            chunk_type_counts.get(chunk_type, 0) + 1
        )

    # ============================================================
    # 14. FINAL OUTPUT
    # ============================================================

    print()
    print("=" * 80)
    print("PDF FULL PIPELINE TEST PASSED")
    print("=" * 80)

    print(
        "Source elements :",
        len(extraction_result.elements),
    )

    print(
        "Final chunks    :",
        len(final_chunks),
    )

    print()
    print("Chunk types:")

    for chunk_type, count in chunk_type_counts.items():

        print(
            f"  {chunk_type}: {count}"
        )

    print()
    print("=" * 80)

