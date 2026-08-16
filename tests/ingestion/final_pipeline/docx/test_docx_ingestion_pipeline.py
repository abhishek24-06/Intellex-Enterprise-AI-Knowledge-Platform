from pathlib import Path

from app.models.documents import Document
from app.enums.enums import (
    DocumentStatus,
    DocumentType,
    DocumentVisibility,
)
from app.services.extraction.extraction_factory import ExtractorFactory
from app.services.cleaning.element_cleaner import ElementCleaner

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

from app.services.pipeline.document_chunker_pipeline import (
    DocumentChunker,
)

from app.services.ingestion.ingestion_dependencies import (
    DocumentIngestionPipeline,
)

from app.services.ingestion.metadata.metadata_enricher import (
    MetadataEnricher,
)

from app.services.ingestion.metadata.chunk_attacher import (
    ChunkContextAttacher,
)

from app.enums.chunk_type import ChunkType


# ============================================================================
# REAL DOCX DOCUMENT
# ============================================================================

TEST_DOCX = Path(
    "tests/doc_test/report.docx"
)


# ============================================================================
# REAL DOCUMENT CHUNKER
# ============================================================================

def build_real_document_chunker() -> DocumentChunker:
    """
    Build the exact real DocumentChunker dependency graph.
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
    Build the complete real ingestion pipeline.

    Document
        ↓
    ExtractorFactory
        ↓
    Extractor
        ↓
    ExtractionResult
        ↓
    ElementCleaner
        ↓
    DocumentChunker
        ↓
    MetadataEnricher
        ↓
    ChunkContextAttacher
        ↓
    FinalChunk[]
    """

    extractor_factory = ExtractorFactory()

    element_cleaner = ElementCleaner()

    document_chunker = (
        build_real_document_chunker()
    )

    metadata_enricher = MetadataEnricher()

    context_attacher = ChunkContextAttacher()

    return DocumentIngestionPipeline(
        extractor_factory=extractor_factory,
        element_cleaner=element_cleaner,
        document_chunker=document_chunker,
        metadata_enricher=metadata_enricher,
        context_attacher=context_attacher,
    )


# ============================================================================
# REAL DOCUMENT OBJECT
# ============================================================================

def build_real_document() -> Document:
    """
    Build a persisted-Document-like object.

    No database is used here.

    The ingestion pipeline only needs the authoritative
    document-level information required for validation,
    extraction selection and context attachment.
    """

    assert TEST_DOCX.exists(), (
        f"Real test document does not exist: {TEST_DOCX}"
    )

    return Document(
        document_id=1001,
        organization_id=10,
        uploaded_by=5,

        document_type=DocumentType.REPORT,

        visibility=DocumentVisibility.RESTRICTED,

        title="Real DOCX Full Pipeline Test",

        description=(
            "Real DOCX integration test for the complete "
            "document ingestion pipeline."
        ),

        original_filename=TEST_DOCX.name,

        stored_filename=TEST_DOCX.name,

        status=DocumentStatus.PROCESSING,

        file_path=str(TEST_DOCX),

        file_size=TEST_DOCX.stat().st_size,

        mime_type=(
            "application/"
            "vnd.openxmlformats-officedocument."
            "wordprocessingml.document"
        ),

        version=1,
    )


# ============================================================================
# TEST
# ============================================================================

def test_real_docx_from_document_to_final_ingestion_output():
    """
    Full real-document integration test.

    Document
        ↓
    ExtractorFactory
        ↓
    DocxExtractor
        ↓
    ExtractionResult
        ↓
    ElementCleaner
        ↓
    StructureDetector
        ↓
    DocumentStructureBuilder
        ↓
    HierarchyChunker / SemanticChunker
        ↓
    ElementRouter
        ↓
    Specialized Chunkers
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
    # STEP 1 — BUILD REAL DOCUMENT
    # ========================================================================

    document = build_real_document()

    assert document.document_id == 1001

    assert document.organization_id == 10

    assert document.uploaded_by == 5

    assert document.mime_type == (
        "application/"
        "vnd.openxmlformats-officedocument."
        "wordprocessingml.document"
    )

    assert document.original_filename == TEST_DOCX.name

    assert document.version == 1

    assert document.file_path == str(TEST_DOCX)


    # ========================================================================
    # STEP 2 — BUILD REAL INGESTION PIPELINE
    # ========================================================================

    pipeline = (
        build_real_ingestion_pipeline()
    )


    # ========================================================================
    # STEP 3 — RUN COMPLETE PIPELINE
    # ========================================================================

    final_chunks = pipeline.ingest(
        document
    )


    # ========================================================================
    # STEP 4 — BASIC FINAL OUTPUT CHECKS
    # ========================================================================

    assert final_chunks is not None

    assert isinstance(
        final_chunks,
        list,
    )

    assert final_chunks


    # ========================================================================
    # STEP 5 — EVERY FINAL CHUNK MUST BE VALID
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

        # Supported final chunk types only.
        assert chunk.chunk_type in {
            ChunkType.NARRATIVE,
            ChunkType.TABLE,
            ChunkType.CODE,
        }

        # Source position must be valid.
        assert chunk.order_index >= 0

        # section_path must always be a list.
        assert isinstance(
            chunk.section_path,
            list,
        )


    # ========================================================================
    # STEP 6 — SOURCE ELEMENT ORDER
    # ========================================================================

    source_elements = []

    for chunk in final_chunks:

        source_elements.extend(
            chunk.elements
        )

    assert source_elements

    source_order_indexes = [
        element.order_index
        for element in source_elements
    ]

    assert all(
        index >= 0
        for index in source_order_indexes
    )


    # ========================================================================
    # STEP 7 — FINAL CHUNKS MUST BE ORDERED
    # ========================================================================

    final_order_indexes = [
        chunk.order_index
        for chunk in final_chunks
    ]

    assert final_order_indexes == sorted(
        final_order_indexes
    )


    # ========================================================================
    # STEP 8 — ORDER INDEX CONTRACT
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
    # STEP 9 — DOCUMENT CONTEXT
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
    # STEP 10 — CONTEXT MUST BE CONSISTENT
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
    # STEP 11 — DOCX PROVENANCE
    # ========================================================================

    # At least one final chunk must retain DOCX provenance.
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
    # STEP 12 — SPECIALIZED CHUNKS
    # ========================================================================

    final_chunk_types = {
        chunk.chunk_type
        for chunk in final_chunks
    }

    assert (
        ChunkType.NARRATIVE
        in final_chunk_types
    )


    # ========================================================================
    # STEP 13 — SECTION PATH DIAGNOSTIC
    # ========================================================================

    print()
    print("=" * 80)
    print("SECTION PATH DIAGNOSTIC")
    print("=" * 80)

    non_empty_section_paths = []

    for chunk in final_chunks:

        if chunk.section_path:

            non_empty_section_paths.append(
                (
                    chunk.order_index,
                    chunk.section_path,
                    chunk.text[:100],
                )
            )

    print(
        "Chunks with non-empty section_path:",
        len(non_empty_section_paths),
    )

    for (
        order_index,
        section_path,
        text_preview,
    ) in non_empty_section_paths[:30]:

        print()
        print(
            f"order_index : {order_index}"
        )

        print(
            f"section_path: {section_path}"
        )

        print(
            f"text        : {text_preview!r}"
        )

    print("=" * 80)


    # ========================================================================
    # STEP 14 — SECTION PATH SHOULD EXIST FOR A STRUCTURED DOCX
    # ========================================================================

    heading_elements = [
        element
        for element in source_elements
        if str(element.element_type).upper().endswith(
            "HEADING"
        )
    ]

    print()
    print(
        "Heading elements found:",
        len(heading_elements),
    )

    for heading in heading_elements[:20]:

        print(
            f"HEADING "
            f"{heading.order_index}: "
            f"{heading.text!r} "
            f"level={heading.metadata.get('level')}"
        )


    # IMPORTANT:
    #
    # Do NOT assert that every chunk has a non-empty section_path.
    #
    # Some document-level content may legitimately exist outside
    # a heading.
    #
    # Instead, if the document contains headings, at least one
    # final chunk should carry hierarchy information.
    #
    # This assertion is intentionally useful for catching the
    # current DOCX section_path bug.

    assert heading_elements, (
        "The DOCX fixture must contain headings "
        "for this section-path integration test."
    )

    assert non_empty_section_paths, (
        "DOCX contains heading elements but no final chunk "
        "contains a non-empty section_path. "
        "This indicates that the structured hierarchy is not "
        "reaching the final chunk pipeline."
    )


    # ========================================================================
    # STEP 15 — FINAL OUTPUT MUST BE USEFUL
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
    # FINAL SUMMARY
    # ========================================================================

    print()
    print("=" * 80)
    print("REAL DOCX → COMPLETE INGESTION PIPELINE")
    print("=" * 80)

    print(
        f"Document ID    : {document.document_id}"
    )

    print(
        f"Source file    : {document.original_filename}"
    )

    print(
        f"MIME type      : {document.mime_type}"
    )

    print(
        f"Final chunks   : {len(final_chunks)}"
    )

    print(
    "Chunk types    : "
    f"{sorted(chunk_type.value for chunk_type in final_chunk_types)}"
)

    print(
        f"Total text     : {total_text_length} chars"
    )

    print(
        f"Headings found : {len(heading_elements)}"
    )

    print(
        "Section paths  : "
        f"{len(non_empty_section_paths)} chunks"
    )

    print(
        "Context        : attached to all chunks"
    )

    print(
        "Validation     : passed"
    )

    print("=" * 80)