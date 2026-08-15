from pathlib import Path

from app.services.extraction.docx_extractor import DocxExtractor

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

from app.services.ingestion.document_ingestion_pipeline import (
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


# ============================================================================
# REAL DOCUMENT
# ============================================================================

TEST_DOCX = Path(
    "tests/doc_test/report.docx"
)


# ============================================================================
# REAL EXTRACTOR
# ============================================================================

def build_real_extractor() -> DocxExtractor:
    return DocxExtractor()


def extract_real_document():
    """
    Run the actual DOCX extractor against the real test document.
    """

    assert TEST_DOCX.exists(), (
        f"Real test document does not exist: {TEST_DOCX}"
    )

    extractor = build_real_extractor()

    extraction_result = extractor.extract(
        file_path=str(TEST_DOCX),
        document_id="real-docx-full-pipeline-test",
        filename=TEST_DOCX.name,
    )

    assert extraction_result is not None

    assert extraction_result.elements

    return extraction_result


# ============================================================================
# REAL DOCUMENT CHUNKER
# ============================================================================

def build_real_document_chunker() -> DocumentChunker:
    """
    Construct the exact real DocumentChunker used by the existing
    production-style chunking tests.
    """

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
    Complete real pipeline:

        DocumentChunker
            ↓
        MetadataEnricher
            ↓
        ChunkContextAttacher
    """

    document_chunker = (
        build_real_document_chunker()
    )

    metadata_enricher = MetadataEnricher()

    context_attacher = ChunkContextAttacher()

    return DocumentIngestionPipeline(
        document_chunker=document_chunker,
        metadata_enricher=metadata_enricher,
        context_attacher=context_attacher,
    )


# ============================================================================
# REAL UPLOAD CONTEXT
# ============================================================================

def build_real_upload_context() -> ChunkContext:
    """
    Simulates the authoritative context supplied by the upload/document
    service.

    These values do NOT come from the DOCX itself.
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

def test_real_docx_from_extractor_to_final_ingestion_output():
    """
    Full real-document regression test.

    DOCX
      ↓
    Extractor
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
    # STEP 1 — REAL EXTRACTION
    # ========================================================================

    extraction_result = extract_real_document()

    source_elements = extraction_result.elements

    assert source_elements

    # Every extracted element must have a valid position.
    assert all(
        element.order_index >= 0
        for element in source_elements
    )

    source_order_indexes = [
        element.order_index
        for element in source_elements
    ]

    # The extractor's source order must be unique.
    assert len(source_order_indexes) == len(
        set(source_order_indexes)
    )

    # ========================================================================
    # STEP 2 — REAL INGESTION PIPELINE
    # ========================================================================

    pipeline = (
        build_real_ingestion_pipeline()
    )

    context = (
        build_real_upload_context()
    )

    final_chunks = pipeline.process(
        extraction_result,
        context,
    )

    # ========================================================================
    # STEP 3 — BASIC FINAL OUTPUT CHECKS
    # ========================================================================

    assert final_chunks is not None

    assert isinstance(
        final_chunks,
        list,
    )

    assert final_chunks

    # ========================================================================
    # STEP 4 — EVERY FINAL CHUNK MUST BE VALID
    # ========================================================================

    for chunk in final_chunks:

        # Text must survive the entire pipeline.
        assert chunk.text is not None

        assert chunk.text.strip()

        # Every chunk must retain source elements.
        assert chunk.elements

        # Metadata must remain a dictionary.
        assert isinstance(
            chunk.metadata,
            dict,
        )

        # Only supported final chunk types may exist.
        assert chunk.chunk_type in {
            ChunkType.NARRATIVE,
            ChunkType.TABLE,
            ChunkType.CODE,
        }

        # Source position must be valid.
        assert chunk.order_index >= 0

        # Section path remains a list.
        assert isinstance(
            chunk.section_path,
            list,
        )

    # ========================================================================
    # STEP 5 — FINAL CHUNKS MUST REFER TO REAL SOURCE ELEMENTS
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
    # STEP 6 — ORDER INDEX MUST REPRESENT DOCUMENT POSITION
    # ========================================================================

    final_order_indexes = [
        chunk.order_index
        for chunk in final_chunks
    ]

    assert final_order_indexes == sorted(
        final_order_indexes
    )

    # Every FinalChunk order_index must correspond to the earliest source
    # element represented by that chunk.
    #
    # Multiple chunks are allowed to share an order_index because a single
    # source element can be split into multiple fragments.
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
    # STEP 7 — DOCUMENT CONTEXT MUST EXIST ON EVERY CHUNK
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
    # STEP 8 — CONTEXT MUST BE CONSISTENT ACROSS THE DOCUMENT
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
    # STEP 9 — EXTRACTOR PROVENANCE MUST SURVIVE
    # ========================================================================

    # The DOCX extractor establishes these fields on its source elements.
    assert all(
        element.metadata.get("source") == "docx"
        for element in source_elements
    )

    assert all(
        element.metadata.get("filename")
        == TEST_DOCX.name
        for element in source_elements
    )

    # At least one final chunk must retain the DOCX provenance.
    assert any(
        chunk.metadata.get("source") == "docx"
        for chunk in final_chunks
    )

    assert any(
        chunk.metadata.get("filename")
        == TEST_DOCX.name
        for chunk in final_chunks
    )

    # ========================================================================
    # STEP 10 — CHECK THAT SPECIALIZED CHUNKS EXIST WHEN PRESENT
    # ========================================================================

    source_element_types = {
        element.element_type
        for element in source_elements
    }

    final_chunk_types = {
        chunk.chunk_type
        for chunk in final_chunks
    }

    # If the real document contains tables, the final pipeline must preserve
    # them as TABLE chunks.
    if any(
        str(element_type).upper().endswith("TABLE")
        for element_type in source_element_types
    ):
        assert (
            ChunkType.TABLE in final_chunk_types
        )

    # If the real document contains code blocks, the final pipeline must
    # preserve them as CODE chunks.
    if any(
        str(element_type).upper().endswith(
            "CODE_BLOCK"
        )
        for element_type in source_element_types
    ):
        assert (
            ChunkType.CODE in final_chunk_types
        )

    # ========================================================================
    # STEP 11 — FINAL OUTPUT MUST BE NON-EMPTY AND USEFUL
    # ========================================================================

    total_text_length = sum(
        len(chunk.text)
        for chunk in final_chunks
    )

    assert total_text_length > 0

    # Every chunk must contain at least one source element.
    assert all(
        len(chunk.elements) >= 1
        for chunk in final_chunks
    )

    # ========================================================================
    # FINAL SUMMARY
    # ========================================================================

    print()
    print("=" * 70)
    print("REAL DOCX → FULL INGESTION PIPELINE")
    print("=" * 70)

    print(
        f"Source elements : {len(source_elements)}"
    )

    print(
        f"Final chunks    : {len(final_chunks)}"
    )

    print(
        "Chunk types     : "
        f"{sorted(chunk_type.value for chunk_type in final_chunk_types)}"
    )

    print(
        f"Total text      : {total_text_length} chars"
    )

    print(
        "Context         : attached to all chunks"
    )

    print(
        "Validation      : passed"
    )

    print("=" * 70)