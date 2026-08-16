from pathlib import Path

from app.services.extraction.markdown_extractor import (
    MarkdownExtractor,
)

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

from app.services.pipeline.document_ingestion_pipeline import (
    DocumentIngestionPipeline,
)

from app.services.ingestion.metadata.metadata_enricher import (
    MetadataEnricher,
)

from app.services.ingestion.metadata.chunk_attacher import (
    ChunkContextAttacher,
)

from app.dto.chunk_context import (
    ChunkContext,
)

from app.enums.chunk_type import (
    ChunkType,
)

from app.enums.enums import (
    DocumentVisibility,
)

from app.enums.element_type import (
    ElementType,
)


# ============================================================================
# REAL MARKDOWN DOCUMENT
# ============================================================================

MD_PATH = Path(
    "tests/md_test/sample.md"
)


# ============================================================================
# REAL MARKDOWN EXTRACTION
# ============================================================================

def extract_real_markdown():
    """
    Run the actual MarkdownExtractor against the real Markdown fixture.
    """

    assert MD_PATH.exists(), (
        f"Real Markdown document not found: {MD_PATH}"
    )

    extractor = MarkdownExtractor()

    extraction_result = extractor.extract(
        file_path=MD_PATH,
        document_id="real-md-full-pipeline-test",
        filename=MD_PATH.name,
    )

    assert extraction_result is not None

    assert extraction_result.elements

    return extraction_result


# ============================================================================
# REAL DOCUMENT CHUNKER
# ============================================================================

def build_real_document_chunker() -> DocumentChunker:
    """
    Build the same real DocumentChunker dependency graph used by
    the already-passing DOCX and PDF full-pipeline tests.
    """

    structure_detector = (
        StructureDetector()
    )

    structure_builder = (
        DocumentStructureBuilder()
    )

    hierarchy_chunker = (
        HierarchyChunker()
    )

    gemini_client = (
        GeminiClient()
    )

    semantic_chunker = (
        SemanticChunker(
            llm_client=gemini_client,
        )
    )

    element_router = (
        ElementRouter()
    )

    narrative_safety_splitter = (
        NarrativeSafetySplitter()
    )

    table_chunker = (
        TableChunker()
    )

    code_chunker = (
        CodeChunker()
    )

    final_chunk_validator = (
        FinalChunkValidator()
    )

    return DocumentChunker(
        structure_detector=structure_detector,
        structure_builder=structure_builder,
        hierarchy_chunker=hierarchy_chunker,
        semantic_chunker=semantic_chunker,
        element_router=element_router,
        narrative_safety_splitter=(
            narrative_safety_splitter
        ),
        table_chunker=table_chunker,
        code_chunker=code_chunker,
        final_chunk_validator=(
            final_chunk_validator
        ),
    )


# ============================================================================
# REAL INGESTION PIPELINE
# ============================================================================

def build_real_ingestion_pipeline() -> DocumentIngestionPipeline:
    """
    Complete Phase 5 pipeline:

        DocumentChunker
            ↓
        MetadataEnricher
            ↓
        ChunkContextAttacher
    """

    document_chunker = (
        build_real_document_chunker()
    )

    metadata_enricher = (
        MetadataEnricher()
    )

    context_attacher = (
        ChunkContextAttacher()
    )

    return DocumentIngestionPipeline(
        document_chunker=document_chunker,
        metadata_enricher=metadata_enricher,
        context_attacher=context_attacher,
    )


# ============================================================================
# UPLOAD / DOCUMENT CONTEXT
# ============================================================================

def build_upload_context() -> ChunkContext:
    """
    Simulates authoritative context supplied by the document/upload
    service.

    This information does not come from Markdown extraction.
    """

    return ChunkContext(
        document_id=1001,
        organization_id=10,
        uploaded_by=5,
        visibility=DocumentVisibility.RESTRICTED,
        document_version=1,
    )


# ============================================================================
# TEST
# ============================================================================

def test_real_markdown_from_extractor_to_final_ingestion_output():
    """
    Full real Markdown regression test.

    Markdown
       ↓
    MarkdownExtractor
       ↓
    ExtractionResult
       ↓
    DocumentChunker
       ↓
    FinalChunkValidator
       ↓
    MetadataEnricher
       ↓
    ChunkContextAttacher
       ↓
    FinalChunk[]
    """

    # ========================================================================
    # STEP 1 — REAL MARKDOWN EXTRACTION
    # ========================================================================

    extraction_result = (
        extract_real_markdown()
    )

    source_elements = (
        extraction_result.elements
    )

    assert source_elements

    # ========================================================================
    # STEP 2 — EXTRACTION ORDERING
    # ========================================================================

    source_order_indexes = [
        element.order_index
        for element in source_elements
    ]

    assert all(
        order_index >= 0
        for order_index in source_order_indexes
    )

    assert source_order_indexes == sorted(
        source_order_indexes
    )

    assert len(source_order_indexes) == len(
        set(source_order_indexes)
    )

    # ========================================================================
    # STEP 3 — MARKDOWN PROVENANCE
    # ========================================================================

    assert all(
        element.metadata.get("source")
        == "markdown"
        for element in source_elements
    )

    assert all(
        element.metadata.get("document_id")
        == "real-md-full-pipeline-test"
        for element in source_elements
    )

    assert all(
        element.metadata.get("filename")
        == MD_PATH.name
        for element in source_elements
    )

    # ========================================================================
    # STEP 4 — ELEMENT TEXT INTEGRITY
    # ========================================================================

    for element in source_elements:

        assert element.text is not None

        assert isinstance(
            element.text,
            str,
        )

    # ========================================================================
    # STEP 5 — SUPPORTED ELEMENT TYPES
    # ========================================================================

    supported_element_types = {
        ElementType.HEADING,
        ElementType.PARAGRAPH,
        ElementType.LIST,
        ElementType.QUOTE,
        ElementType.CODE_BLOCK,
        ElementType.TABLE,
    }

    for element in source_elements:

        assert (
            element.element_type
            in supported_element_types
        )

    # ========================================================================
    # STEP 6 — HEADING METADATA
    # ========================================================================

    headings = [
        element
        for element in source_elements
        if element.element_type
        == ElementType.HEADING
    ]

    for heading in headings:

        level = heading.metadata.get(
            "level"
        )

        assert level is not None

        assert isinstance(
            level,
            int,
        )

        assert 1 <= level <= 6

    # ========================================================================
    # STEP 7 — LIST METADATA
    # ========================================================================

    lists = [
        element
        for element in source_elements
        if element.element_type
        == ElementType.LIST
    ]

    for list_element in lists:

        assert isinstance(
            list_element.metadata.get(
                "ordered"
            ),
            bool,
        )

        indent_level = (
            list_element.metadata.get(
                "indent_level"
            )
        )

        assert indent_level is not None

        assert isinstance(
            indent_level,
            int,
        )

        assert indent_level >= 0

    # ========================================================================
    # STEP 8 — CODE METADATA
    # ========================================================================

    code_blocks = [
        element
        for element in source_elements
        if element.element_type
        == ElementType.CODE_BLOCK
    ]

    for code_block in code_blocks:

        assert (
            "language"
            in code_block.metadata
        )

    # ========================================================================
    # STEP 9 — TABLE METADATA
    # ========================================================================

    source_tables = [
        element
        for element in source_elements
        if element.element_type
        == ElementType.TABLE
    ]

    for table in source_tables:

        metadata = table.metadata

        assert metadata.get(
            "table_id"
        )

        assert (
            metadata.get("table_index")
            is not None
        )

        assert (
            metadata.get("n_rows")
            is not None
        )

        assert (
            metadata.get("n_cols")
            is not None
        )

        assert isinstance(
            metadata.get("cells"),
            list,
        )

        assert isinstance(
            metadata.get("has_header_row"),
            bool,
        )

        assert metadata.get(
            "markdown"
        ) is not None

    # ========================================================================
    # STEP 10 — REAL INGESTION PIPELINE
    # ========================================================================

    pipeline = (
        build_real_ingestion_pipeline()
    )

    context = (
        build_upload_context()
    )

    final_chunks = pipeline.process(
        extraction_result,
        context,
    )

    # ========================================================================
    # STEP 11 — FINAL OUTPUT SANITY
    # ========================================================================

    assert final_chunks is not None

    assert isinstance(
        final_chunks,
        list,
    )

    assert final_chunks

    # ========================================================================
    # STEP 12 — EVERY FINAL CHUNK MUST BE VALID
    # ========================================================================

    for chunk in final_chunks:

        assert chunk.text is not None

        assert chunk.text.strip()

        assert chunk.elements

        assert isinstance(
            chunk.metadata,
            dict,
        )

        assert chunk.chunk_type in {
            ChunkType.NARRATIVE,
            ChunkType.TABLE,
            ChunkType.CODE,
        }

        assert chunk.order_index >= 0

        assert isinstance(
            chunk.section_path,
            list,
        )

    # ========================================================================
    # STEP 13 — FINAL CHUNKS MUST REFER TO REAL SOURCE ELEMENTS
    # ========================================================================

    source_order_index_set = {
        element.order_index
        for element in source_elements
    }

    for chunk in final_chunks:

        for element in chunk.elements:

            assert (
                element.order_index
                in source_order_index_set
            )

    # ========================================================================
    # STEP 14 — FINAL ORDER
    # ========================================================================

    final_order_indexes = [
        chunk.order_index
        for chunk in final_chunks
    ]

    assert final_order_indexes == sorted(
        final_order_indexes
    )

    # ========================================================================
    # STEP 15 — ORDER INDEX MUST MATCH SOURCE POSITION
    # ========================================================================

    for chunk in final_chunks:

        minimum_source_order = min(
            element.order_index
            for element in chunk.elements
        )

        assert (
            chunk.order_index
            == minimum_source_order
        )

    # ========================================================================
    # STEP 16 — DOCUMENT CONTEXT ON EVERY CHUNK
    # ========================================================================

    for chunk in final_chunks:

        assert (
            chunk.metadata["document_id"]
            == 1001
        )

        assert (
            chunk.metadata["organization_id"]
            == 10
        )

        assert (
            chunk.metadata["uploaded_by"]
            == 5
        )

        assert (
            chunk.metadata["visibility"]
            == DocumentVisibility.RESTRICTED.value
        )

        assert (
            chunk.metadata["document_version"]
            == 1
        )

    # ========================================================================
    # STEP 17 — CONTEXT CONSISTENCY
    # ========================================================================

    assert {
        chunk.metadata["document_id"]
        for chunk in final_chunks
    } == {1001}

    assert {
        chunk.metadata["organization_id"]
        for chunk in final_chunks
    } == {10}

    assert {
        chunk.metadata["uploaded_by"]
        for chunk in final_chunks
    } == {5}

    assert {
        chunk.metadata["visibility"]
        for chunk in final_chunks
    } == {
        DocumentVisibility.RESTRICTED.value
    }

    assert {
        chunk.metadata["document_version"]
        for chunk in final_chunks
    } == {1}

    # ========================================================================
    # STEP 18 — EXTRACTOR PROVENANCE MUST SURVIVE
    # ========================================================================

    assert any(
        chunk.metadata.get("source")
        == "markdown"
        for chunk in final_chunks
    )

    assert any(
        chunk.metadata.get("filename")
        == MD_PATH.name
        for chunk in final_chunks
    )

    # ========================================================================
    # STEP 19 — TABLE CHUNKS
    # ========================================================================

    if source_tables:

        final_table_chunks = [
            chunk
            for chunk in final_chunks
            if chunk.chunk_type
            == ChunkType.TABLE
        ]

        assert final_table_chunks

        for chunk in final_table_chunks:

            assert chunk.metadata.get(
                "is_table_chunk"
            ) is True

            assert (
                chunk.metadata.get(
                    "table_chunk_index"
                )
                is not None
            )

            assert (
                chunk.metadata.get(
                    "table_chunk_count"
                )
                is not None
            )

    # ========================================================================
    # STEP 20 — CODE CHUNKS
    # ========================================================================

    if code_blocks:

        final_code_chunks = [
            chunk
            for chunk in final_chunks
            if chunk.chunk_type
            == ChunkType.CODE
        ]

        assert final_code_chunks

    # ========================================================================
    # STEP 21 — TOTAL CONTENT
    # ========================================================================

    total_text_length = sum(
        len(chunk.text)
        for chunk in final_chunks
    )

    assert total_text_length > 0

    assert all(
        len(chunk.elements) >= 1
        for chunk in final_chunks
    )

    # ========================================================================
    # STEP 22 — FINAL SUMMARY
    # ========================================================================

    final_chunk_types = {
        chunk.chunk_type
        for chunk in final_chunks
    }

    print()
    print("=" * 70)
    print("REAL MARKDOWN → FULL INGESTION PIPELINE")
    print("=" * 70)

    print(
        f"Source elements : {len(source_elements)}"
    )

    print(
        f"Final chunks    : {len(final_chunks)}"
    )

    print(
        "Element types   : "
        f"{sorted(str(e.element_type) for e in source_elements)}"
    )

    print(
        "Chunk types     : "
        f"{sorted(chunk_type.value for chunk_type in final_chunk_types)}"
    )

    print(
        f"Tables extracted: {len(source_tables)}"
    )

    print(
        f"Code blocks     : {len(code_blocks)}"
    )

    print(
        f"Total text      : {total_text_length} chars"
    )

    print(
        "Provenance      : preserved"
    )

    print(
        "Context         : attached to all chunks"
    )

    print(
        "Validation      : passed"
    )

    print("=" * 70)