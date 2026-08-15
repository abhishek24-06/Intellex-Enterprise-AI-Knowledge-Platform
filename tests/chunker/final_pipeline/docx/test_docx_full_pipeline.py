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

from app.enums.chunk_type import ChunkType

from app.services.chunking.final_chunker.document_chunker import (
    DocumentChunker,
)

def test_real_docx_full_pipeline():

    # ---------------------------------------------------------
    # Locate the real DOCX
    # ---------------------------------------------------------

    docx_path = Path("tests/doc_test/report.docx")

    assert docx_path.exists(), (
        f"Test document not found: {docx_path}"
    )

    # ---------------------------------------------------------
    # 1. REAL DOCX EXTRACTION
    # ---------------------------------------------------------

    extractor = DocxExtractor()

    extraction_result = extractor.extract(
        file_path=str(docx_path),
        document_id="e2e-docx-test",
        filename="report.docx",
    )

    # ---------------------------------------------------------
    # Extraction sanity checks
    # ---------------------------------------------------------

    assert extraction_result.elements

    assert all(
        element.order_index >= 0
        for element in extraction_result.elements
    )

    order_indexes = [
        element.order_index
        for element in extraction_result.elements
    ]

    assert len(order_indexes) == len(set(order_indexes))

    # Verify DOCX provenance made it through extraction.
    assert all(
        element.metadata.get("source") == "docx"
        for element in extraction_result.elements
    )

    assert all(
        element.metadata.get("filename") == "report.docx"
        for element in extraction_result.elements
    )

    # ---------------------------------------------------------
    # 2. REAL CHUNKING PIPELINE
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # 3. REAL EXTRACTION RESULT → REAL DOCUMENT CHUNKER
    # ---------------------------------------------------------

    final_chunks = document_chunker.chunk(
        extraction_result
    )

    # ---------------------------------------------------------
    # 4. BASIC FINAL OUTPUT INVARIANTS
    # ---------------------------------------------------------

    assert final_chunks

    assert all(
        chunk.text.strip()
        for chunk in final_chunks
    )

    assert all(
        chunk.elements
        for chunk in final_chunks
    )

    # ---------------------------------------------------------
    # 5. FINAL CHUNKS MUST BE ORDERED
    # ---------------------------------------------------------

    chunk_order_indexes = [
        chunk.order_index
        for chunk in final_chunks
    ]

    assert chunk_order_indexes == sorted(
        chunk_order_indexes
    )

    # ---------------------------------------------------------
    # 6. EVERY CHUNK MUST HAVE A VALID TYPE
    # ---------------------------------------------------------

    valid_types = {
        ChunkType.NARRATIVE,
        ChunkType.TABLE,
        ChunkType.CODE,
    }

    assert all(
        chunk.chunk_type in valid_types
        for chunk in final_chunks
    )

    # ---------------------------------------------------------
    # 7. EVERY FINAL CHUNK MUST POINT TO REAL SOURCE ELEMENTS
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # 8. CHUNK ORDER MUST MATCH FIRST SOURCE ELEMENT
    # ---------------------------------------------------------

    for chunk in final_chunks:

        minimum_source_order = min(
            element.order_index
            for element in chunk.elements
        )

        assert (
            chunk.order_index
            == minimum_source_order
        )

    # ---------------------------------------------------------
    # 9. METADATA MUST SURVIVE
    # ---------------------------------------------------------

    for chunk in final_chunks:

        assert isinstance(
            chunk.metadata,
            dict,
        )

        for element in chunk.elements:

            if element.metadata.get("document_id"):

                assert (
                    chunk.metadata.get("document_id")
                    == element.metadata.get("document_id")
                )

    # ---------------------------------------------------------
    # 10. EXPLICIT VALIDATOR RUN
    # ---------------------------------------------------------
    #
    # DocumentChunker already invokes this internally.
    # Running it again here makes this E2E test explicit:
    #
    # REAL EXTRACTOR
    #      ↓
    # REAL CHUNKING
    #      ↓
    # REAL FINAL CHUNKS
    #      ↓
    # REAL VALIDATOR
    #

    validator.validate(
        chunks=final_chunks,
        source_elements=extraction_result.elements,
    )


    chunk_type_counts = {
        chunk_type: sum(
            chunk.chunk_type == chunk_type
            for chunk in final_chunks
        )
        for chunk_type in valid_types
    }

    print("\nFinal chunk distribution:")
    for chunk_type, count in chunk_type_counts.items():
        print(f"  {chunk_type.value}: {count}")


#####################################
        element_type_counts = {}

    for element in extraction_result.elements:

        element_type = element.element_type

        element_type_counts[element_type] = (
            element_type_counts.get(element_type, 0) + 1
        )

    print("\nExtracted element distribution:")

    for element_type, count in element_type_counts.items():
        print(
            f"  {element_type}: {count}"
        )

    print(
        f"\nExtracted elements: "
        f"{len(extraction_result.elements)}"
    )

    print(
        f"Final chunks: "
        f"{len(final_chunks)}"
    )

    validator.validate(
    chunks=final_chunks,
    source_elements=extraction_result.elements,
)

        # ---------------------------------------------------------
    # 11. SAMPLE REAL FINAL CHUNKS
    # ---------------------------------------------------------

    print("\n" + "=" * 80)
    print("SAMPLE FINAL CHUNKS")
    print("=" * 80)

    for chunk_type in (
        ChunkType.NARRATIVE,
        ChunkType.TABLE,
        ChunkType.CODE,
    ):

        matching_chunks = [
            chunk
            for chunk in final_chunks
            if chunk.chunk_type == chunk_type
        ]

        print(
            f"\n\n{'#' * 20} "
            f"{chunk_type.value.upper()} "
            f"{'#' * 20}"
        )

        # First 3 chunks
        for i, chunk in enumerate(
            matching_chunks[:3]
        ):

            print("\n" + "-" * 80)

            print(
                f"Chunk #{i + 1}"
            )

            print(
                f"order_index: {chunk.order_index}"
            )

            print(
                f"section_path: {chunk.section_path}"
            )

            print(
                f"metadata: {chunk.metadata}"
            )

            print(
                f"source_elements: "
                f"{[e.order_index for e in chunk.elements]}"
            )

            print(
                f"text_length: {len(chunk.text)}"
            )

            print("\nTEXT:")

            print(chunk.text[:2000])

        # ---------------------------------------------------------
    # 12. LARGEST CHUNKS
    # ---------------------------------------------------------

    largest_chunks = sorted(
        final_chunks,
        key=lambda chunk: len(chunk.text),
        reverse=True,
    )[:10]

    print("\n" + "=" * 80)
    print("10 LARGEST FINAL CHUNKS")
    print("=" * 80)

    for i, chunk in enumerate(
        largest_chunks,
        start=1,
    ):

        print("\n" + "-" * 80)

        print(
            f"{i}. "
            f"type={chunk.chunk_type.value} "
            f"order={chunk.order_index} "
            f"chars={len(chunk.text)}"
        )

        print(
            f"section_path={chunk.section_path}"
        )

        print(
            chunk.text[:500]
        )