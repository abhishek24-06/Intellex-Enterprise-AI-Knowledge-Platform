from pathlib import Path

from app.services.extraction.markdown_extractor import MarkdownExtractor

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


def test_real_markdown_full_pipeline():

    # ============================================================
    # 1. LOCATE REAL MARKDOWN FILE
    # ============================================================

    test_dir = Path(__file__).parent

    markdown_path = test_dir / "sample.md"

    assert markdown_path.exists(), (
        f"Test Markdown file not found: {markdown_path}"
    )

    # ============================================================
    # 2. REAL MARKDOWN EXTRACTION
    # ============================================================

    extractor = MarkdownExtractor()

    extraction_result = extractor.extract(
        file_path=markdown_path,
        document_id="e2e-markdown-test",
        filename=markdown_path.name,
    )

    # ============================================================
    # 3. EXTRACTION SANITY CHECKS
    # ============================================================

    assert extraction_result is not None

    assert extraction_result.elements

    # ------------------------------------------------------------
    # Every extracted element must have a valid order index
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
    # Markdown provenance
    # ------------------------------------------------------------

    assert all(
        element.metadata.get("source") == "markdown"
        for element in extraction_result.elements
    )

    assert all(
        element.metadata.get("filename") == markdown_path.name
        for element in extraction_result.elements
    )

    # ============================================================
    # 4. VERIFY EXPECTED MARKDOWN ELEMENT TYPES
    # ============================================================

    element_types = {
        element.element_type
        for element in extraction_result.elements
    }

    # These should exist in the Markdown fixture.
    assert ElementType.HEADING in element_types
    assert ElementType.PARAGRAPH in element_types
    assert ElementType.LIST in element_types
    assert ElementType.QUOTE in element_types
    assert ElementType.CODE_BLOCK in element_types
    assert ElementType.TABLE in element_types

    # ============================================================
    # 5. MARKDOWN-SPECIFIC CODE LANGUAGE CHECK
    # ============================================================

    code_elements = [
        element
        for element in extraction_result.elements
        if element.element_type == ElementType.CODE_BLOCK
    ]

    assert code_elements, (
        "Markdown fixture must contain at least one fenced "
        "code block."
    )

    # At least one fenced code block should have a language.
    known_language_code = [
        element
        for element in code_elements
        if element.metadata.get("language")
    ]

    assert known_language_code, (
        "Markdown fixture must contain at least one "
        "language-tagged fenced code block."
    )

    # ============================================================
    # 6. BUILD REAL CHUNKING PIPELINE
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
    # 7. EXTRACTION RESULT → DOCUMENT CHUNKER
    # ============================================================

    final_chunks = document_chunker.chunk(
        extraction_result
    )

    # ============================================================
    # 8. BASIC FINAL CHUNK SANITY CHECKS
    # ============================================================

    assert final_chunks

    assert all(
        chunk.text.strip()
        for chunk in final_chunks
    )

    assert all(
        chunk.elements
        for chunk in final_chunks
    )

    # ============================================================
    # 9. FINAL CHUNKS MUST BE ORDERED
    # ============================================================

    chunk_order_indexes = [
        chunk.order_index
        for chunk in final_chunks
    ]

    assert chunk_order_indexes == sorted(
        chunk_order_indexes
    )

    # ============================================================
    # 10. EVERY CHUNK MUST HAVE A VALID TYPE
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
    # 11. EVERY FINAL CHUNK MUST POINT TO REAL
    #     SOURCE ELEMENTS
    # ============================================================

    source_order_indexes = {
        element.order_index
        for element in extraction_result.elements
        if element.element_type != ElementType.HEADING
    }

    for chunk in final_chunks:

        for element in chunk.elements:

            assert (
                element.order_index
                in source_order_indexes
            )

    # ============================================================
    # 12. CHUNK ORDER MUST MATCH FIRST SOURCE ELEMENT
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
    # 13. METADATA MUST SURVIVE
    # ============================================================

    for chunk in final_chunks:

        assert isinstance(
            chunk.metadata,
            dict,
        )

        for element in chunk.elements:

            document_id = element.metadata.get(
                "document_id"
            )

            if document_id:

                assert (
                    chunk.metadata.get("document_id")
                    == document_id
                )

    # ============================================================
    # 14. VERIFY MARKDOWN CODE LANGUAGE SURVIVES
    #     EXTRACTION → FINAL CHUNK
    # ============================================================

    final_code_chunks = [
        chunk
        for chunk in final_chunks
        if chunk.chunk_type == ChunkType.CODE
    ]

    assert final_code_chunks, (
        "Expected at least one final CODE chunk."
    )

    source_languages = {
        element.metadata.get("language")
        for element in code_elements
        if element.metadata.get("language")
    }

    final_languages = {
        chunk.metadata.get("language")
        for chunk in final_code_chunks
        if chunk.metadata.get("language")
    }

    assert source_languages <= final_languages, (
        "A Markdown code language was lost between "
        "extraction and final chunking."
    )

    # ============================================================
    # 15. VERIFY TABLE CHUNKS EXIST
    # ============================================================

    table_chunks = [
        chunk
        for chunk in final_chunks
        if chunk.chunk_type == ChunkType.TABLE
    ]

    assert table_chunks, (
        "Expected at least one final TABLE chunk."
    )

    # ============================================================
    # 16. VERIFY NARRATIVE CHUNKS EXIST
    # ============================================================

    narrative_chunks = [
        chunk
        for chunk in final_chunks
        if chunk.chunk_type == ChunkType.NARRATIVE
    ]

    assert narrative_chunks, (
        "Expected at least one final NARRATIVE chunk."
    )

    # ============================================================
    # 17. SOURCE COVERAGE
    # ============================================================

    covered_order_indexes = {
        element.order_index
        for chunk in final_chunks
        for element in chunk.elements
    }

    missing_elements = (
        source_order_indexes
        - covered_order_indexes
    )

    # ------------------------------------------------------------
    # Diagnostic output
    #
    # DO NOT weaken the coverage assertion yet.
    #
    # If elements are missing, print their exact:
    #   - order_index
    #   - element_type
    #   - text
    #   - metadata
    #
    # This allows us to determine whether the missing elements
    # are structural elements intentionally consumed by the
    # chunking pipeline or genuine source-content loss.
    # ------------------------------------------------------------

    if missing_elements:

        print("\n" + "=" * 80)
        print("MISSING SOURCE ELEMENTS")
        print("=" * 80)

        print(
            f"\nMissing count: {len(missing_elements)}"
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
                f"\norder_index : {element.order_index}"
            )

            print(
                f"element_type: {element.element_type}"
            )

            print(
                f"text        : {element.text!r}"
            )

            print(
                f"metadata    : {element.metadata}"
            )

        print("\n" + "-" * 80)

        # Also print the final chunk coverage so we can compare
        # source elements against what actually survived.

        print("FINAL CHUNK COVERAGE")
        print("-" * 80)

        for chunk in final_chunks:

            chunk_element_indexes = [
                element.order_index
                for element in chunk.elements
            ]

            print(
                f"\nchunk_type={chunk.chunk_type}"
            )

            print(
                f"order_index={chunk.order_index}"
            )

            print(
                f"source_elements={chunk_element_indexes}"
            )

            print(
                f"text={chunk.text!r}".encode(
                    "ascii",
                    errors="backslashreplace",
                ).decode("ascii")
)
        

        print("\n" + "=" * 80)

    # IMPORTANT:
    # Keep this assertion strict.
    #
    # We want the test to fail until we determine whether the
    # missing elements are intentional structural elements or
    # genuine content loss.
    assert missing_elements == set(), (
        "Source elements were lost during the full "
        "Markdown pipeline: "
        f"{sorted(missing_elements)}"
    )

    # ============================================================
    # 18. EXPLICIT FINAL VALIDATOR RUN
    # ============================================================

    # DocumentChunker already invokes the validator.
    # Running it again makes this E2E test explicit:
    #
    # Markdown Extractor
    #       ↓
    # ExtractionResult
    #       ↓
    # DocumentChunker
    #       ↓
    # FinalChunk[]
    #       ↓
    # FinalChunkValidator

    validator.validate(
        chunks=final_chunks,
        source_elements=extraction_result.elements,
    )

    # ============================================================
    # 19. PRINT FINAL DISTRIBUTION
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
            f"  {chunk_type.value}: {count}"
        )

    # ============================================================
    # 20. PRINT EXTRACTED ELEMENT DISTRIBUTION
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
            f"  {element_type}: {count}"
        )

    # ============================================================
    # 21. SUMMARY
    # ============================================================

    print("\n" + "=" * 80)
    print("MARKDOWN FULL PIPELINE TEST PASSED")
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
        f"Code elements   : "
        f"{len(code_elements)}"
    )

    print(
        f"Code chunks     : "
        f"{len(final_code_chunks)}"
    )

    print(
        f"Table chunks    : "
        f"{len(table_chunks)}"
    )

    print(
        f"Narrative chunks: "
        f"{len(narrative_chunks)}"
    )

    print("=" * 80)