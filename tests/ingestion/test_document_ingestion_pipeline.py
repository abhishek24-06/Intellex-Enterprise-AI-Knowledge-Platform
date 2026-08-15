from unittest.mock import Mock, call

import pytest

from app.dto.final_chunk import FinalChunk
from app.dto.extracted_element import ExtractedElement
from app.enums.chunk_type import ChunkType
from app.enums.element_type import ElementType
from app.enums.enums import DocumentVisibility
from app.services.ingestion.document_ingestion_pipeline import (
    DocumentIngestionPipeline,
)
from app.services.ingestion.metadata.metadata_enricher import (
    MetadataEnricher,
)
from app.dto.chunk_context import ChunkContext 

from app.services.ingestion.metadata.chunk_attacher import ChunkContextAttacher


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_element(
    order_index: int,
    text: str,
    metadata: dict | None = None,
) -> ExtractedElement:
    return ExtractedElement(
        order_index=order_index,
        text=text,
        element_type=ElementType.PARAGRAPH,
        metadata=metadata or {},
    )


def make_final_chunk(
    order_index: int = 0,
    text: str = "Test content",
    metadata: dict | None = None,
    section_path: list[str] | None = None,
    chunk_type: ChunkType = ChunkType.NARRATIVE,
) -> FinalChunk:

    element = make_element(
        order_index=order_index,
        text=text,
        metadata=metadata or {},
    )

    return FinalChunk(
        text=text,
        elements=[element],
        chunk_type=chunk_type,
        section_path=section_path or [],
        order_index=order_index,
        metadata=metadata or {},
    )


def make_extraction_result():
    """
    Minimal mock ExtractionResult.

    The integration tests here are testing orchestration, not extraction.
    """
    return Mock(name="ExtractionResult")


def make_context() -> ChunkContext:
    return ChunkContext(
        document_id=100,
        organization_id=10,
        uploaded_by=5,
        visibility=DocumentVisibility.RESTRICTED,
        document_version=1,
    )


# ---------------------------------------------------------------------------
# Basic pipeline execution
# ---------------------------------------------------------------------------

def test_pipeline_runs_chunking_then_metadata_then_context():

    extraction_result = make_extraction_result()
    context = make_context()

    chunker = Mock()
    enricher = Mock()
    attacher = Mock()

    initial_chunk = make_final_chunk(
        metadata={
            "source": "pdf",
        }
    )

    enriched_chunk = make_final_chunk(
        metadata={
            "source": "pdf",
            "page": 2,
        }
    )

    final_chunk = make_final_chunk(
        metadata={
            "source": "pdf",
            "page": 2,
            "document_id": 100,
            "organization_id": 10,
            "uploaded_by": 5,
            "visibility": "RESTRICTED",
            "document_version": 1,
        }
    )

    chunker.chunk.return_value = [
        initial_chunk
    ]

    enricher.enrich.return_value = [
        enriched_chunk
    ]

    attacher.attach.return_value = [
        final_chunk
    ]

    pipeline = DocumentIngestionPipeline(
        document_chunker=chunker,
        metadata_enricher=enricher,
        context_attacher=attacher,
    )

    result = pipeline.process(
        extraction_result,
        context,
    )

    assert result == [
        final_chunk
    ]

    chunker.chunk.assert_called_once_with(
        extraction_result
    )

    enricher.enrich.assert_called_once_with(
        [initial_chunk]
    )

    attacher.attach.assert_called_once_with(
        [enriched_chunk],
        context,
    )


# ---------------------------------------------------------------------------
# Empty result
# ---------------------------------------------------------------------------

def test_pipeline_handles_empty_chunk_result():

    extraction_result = make_extraction_result()
    context = make_context()

    chunker = Mock()
    enricher = Mock()
    attacher = Mock()

    chunker.chunk.return_value = []

    enricher.enrich.return_value = []

    attacher.attach.return_value = []

    pipeline = DocumentIngestionPipeline(
        document_chunker=chunker,
        metadata_enricher=enricher,
        context_attacher=attacher,
    )

    result = pipeline.process(
        extraction_result,
        context,
    )

    assert result == []

    chunker.chunk.assert_called_once_with(
        extraction_result
    )

    enricher.enrich.assert_called_once_with([])

    attacher.attach.assert_called_once_with(
        [],
        context,
    )


# ---------------------------------------------------------------------------
# Multiple chunks
# ---------------------------------------------------------------------------

def test_pipeline_processes_all_chunks():

    extraction_result = make_extraction_result()
    context = make_context()

    chunker = Mock()
    enricher = Mock()
    attacher = Mock()

    chunks = [
        make_final_chunk(
            order_index=0,
            text="First",
            metadata={"source": "docx"},
        ),
        make_final_chunk(
            order_index=1,
            text="Second",
            metadata={"source": "docx"},
        ),
        make_final_chunk(
            order_index=2,
            text="Third",
            metadata={"source": "docx"},
        ),
    ]

    enriched_chunks = [
        make_final_chunk(
            order_index=0,
            text="First",
            metadata={
                "source": "docx",
                "page": 1,
            },
        ),
        make_final_chunk(
            order_index=1,
            text="Second",
            metadata={
                "source": "docx",
                "page": 1,
            },
        ),
        make_final_chunk(
            order_index=2,
            text="Third",
            metadata={
                "source": "docx",
                "page": 2,
            },
        ),
    ]

    final_chunks = [
        make_final_chunk(
            order_index=0,
            text="First",
            metadata={
                "source": "docx",
                "page": 1,
                "document_id": 100,
                "organization_id": 10,
                "uploaded_by": 5,
                "visibility": "RESTRICTED",
                "document_version": 1,
            },
        ),
        make_final_chunk(
            order_index=1,
            text="Second",
            metadata={
                "source": "docx",
                "page": 1,
                "document_id": 100,
                "organization_id": 10,
                "uploaded_by": 5,
                "visibility": "RESTRICTED",
                "document_version": 1,
            },
        ),
        make_final_chunk(
            order_index=2,
            text="Third",
            metadata={
                "source": "docx",
                "page": 2,
                "document_id": 100,
                "organization_id": 10,
                "uploaded_by": 5,
                "visibility": "RESTRICTED",
                "document_version": 1,
            },
        ),
    ]

    chunker.chunk.return_value = chunks
    enricher.enrich.return_value = enriched_chunks
    attacher.attach.return_value = final_chunks

    pipeline = DocumentIngestionPipeline(
        document_chunker=chunker,
        metadata_enricher=enricher,
        context_attacher=attacher,
    )

    result = pipeline.process(
        extraction_result,
        context,
    )

    assert result == final_chunks
    assert len(result) == 3

    chunker.chunk.assert_called_once_with(
        extraction_result
    )

    enricher.enrich.assert_called_once_with(
        chunks
    )

    attacher.attach.assert_called_once_with(
        enriched_chunks,
        context,
    )


# ---------------------------------------------------------------------------
# Pipeline ordering
# ---------------------------------------------------------------------------

def test_pipeline_calls_components_in_correct_order():

    extraction_result = make_extraction_result()
    context = make_context()

    execution_order = []

    chunker = Mock()
    enricher = Mock()
    attacher = Mock()

    chunks = [
        make_final_chunk()
    ]

    chunker.chunk.side_effect = lambda result: (
        execution_order.append("chunker"),
        chunks,
    )[1]

    enricher.enrich.side_effect = lambda value: (
        execution_order.append("enricher"),
        value,
    )[1]

    attacher.attach.side_effect = lambda value, ctx: (
        execution_order.append("attacher"),
        value,
    )[1]

    pipeline = DocumentIngestionPipeline(
        document_chunker=chunker,
        metadata_enricher=enricher,
        context_attacher=attacher,
    )

    pipeline.process(
        extraction_result,
        context,
    )

    assert execution_order == [
        "chunker",
        "enricher",
        "attacher",
    ]


# ---------------------------------------------------------------------------
# Data flows between stages
# ---------------------------------------------------------------------------

def test_pipeline_passes_chunker_output_to_enricher():

    extraction_result = make_extraction_result()
    context = make_context()

    chunker = Mock()
    enricher = Mock()
    attacher = Mock()

    chunker_chunks = [
        make_final_chunk(
            metadata={"source": "pdf"}
        )
    ]

    enriched_chunks = [
        make_final_chunk(
            metadata={
                "source": "pdf",
                "page": 3,
            }
        )
    ]

    final_chunks = [
        make_final_chunk(
            metadata={
                "source": "pdf",
                "page": 3,
                "document_id": 100,
            }
        )
    ]

    chunker.chunk.return_value = chunker_chunks
    enricher.enrich.return_value = enriched_chunks
    attacher.attach.return_value = final_chunks

    pipeline = DocumentIngestionPipeline(
        document_chunker=chunker,
        metadata_enricher=enricher,
        context_attacher=attacher,
    )

    pipeline.process(
        extraction_result,
        context,
    )

    enricher.enrich.assert_called_once_with(
        chunker_chunks
    )


def test_pipeline_passes_enricher_output_to_context_attacher():

    extraction_result = make_extraction_result()
    context = make_context()

    chunker = Mock()
    enricher = Mock()
    attacher = Mock()

    chunker_chunks = [
        make_final_chunk()
    ]

    enriched_chunks = [
        make_final_chunk(
            metadata={
                "source": "pdf",
                "page": 5,
            }
        )
    ]

    final_chunks = [
        make_final_chunk()
    ]

    chunker.chunk.return_value = chunker_chunks
    enricher.enrich.return_value = enriched_chunks
    attacher.attach.return_value = final_chunks

    pipeline = DocumentIngestionPipeline(
        document_chunker=chunker,
        metadata_enricher=enricher,
        context_attacher=attacher,
    )

    pipeline.process(
        extraction_result,
        context,
    )

    attacher.attach.assert_called_once_with(
        enriched_chunks,
        context,
    )


# ---------------------------------------------------------------------------
# Output preservation
# ---------------------------------------------------------------------------

def test_pipeline_returns_context_attacher_output_unchanged():

    extraction_result = make_extraction_result()
    context = make_context()

    chunker = Mock()
    enricher = Mock()
    attacher = Mock()

    chunker_output = [
        make_final_chunk(
            metadata={"source": "txt"}
        )
    ]

    enricher_output = [
        make_final_chunk(
            metadata={
                "source": "txt",
                "filename": "test.txt",
            }
        )
    ]

    attacher_output = [
        make_final_chunk(
            metadata={
                "source": "txt",
                "filename": "test.txt",
                "document_id": 100,
                "organization_id": 10,
                "uploaded_by": 5,
                "visibility": "RESTRICTED",
                "document_version": 1,
            }
        )
    ]

    chunker.chunk.return_value = chunker_output
    enricher.enrich.return_value = enricher_output
    attacher.attach.return_value = attacher_output

    pipeline = DocumentIngestionPipeline(
        document_chunker=chunker,
        metadata_enricher=enricher,
        context_attacher=attacher,
    )

    result = pipeline.process(
        extraction_result,
        context,
    )

    assert result is attacher_output


# ---------------------------------------------------------------------------
# Failure propagation
# ---------------------------------------------------------------------------

def test_pipeline_propagates_chunker_failure():

    extraction_result = make_extraction_result()
    context = make_context()

    chunker = Mock()
    enricher = Mock()
    attacher = Mock()

    error = RuntimeError(
        "Chunking failed"
    )

    chunker.chunk.side_effect = error

    pipeline = DocumentIngestionPipeline(
        document_chunker=chunker,
        metadata_enricher=enricher,
        context_attacher=attacher,
    )

    with pytest.raises(
        RuntimeError,
        match="Chunking failed",
    ):
        pipeline.process(
            extraction_result,
            context,
        )

    enricher.enrich.assert_not_called()
    attacher.attach.assert_not_called()


def test_pipeline_propagates_metadata_enricher_failure():

    extraction_result = make_extraction_result()
    context = make_context()

    chunker = Mock()
    enricher = Mock()
    attacher = Mock()

    chunks = [
        make_final_chunk()
    ]

    chunker.chunk.return_value = chunks

    error = RuntimeError(
        "Metadata enrichment failed"
    )

    enricher.enrich.side_effect = error

    pipeline = DocumentIngestionPipeline(
        document_chunker=chunker,
        metadata_enricher=enricher,
        context_attacher=attacher,
    )

    with pytest.raises(
        RuntimeError,
        match="Metadata enrichment failed",
    ):
        pipeline.process(
            extraction_result,
            context,
        )

    attacher.attach.assert_not_called()


def test_pipeline_propagates_context_attachment_failure():

    extraction_result = make_extraction_result()
    context = make_context()

    chunker = Mock()
    enricher = Mock()
    attacher = Mock()

    chunks = [
        make_final_chunk()
    ]

    enriched_chunks = [
        make_final_chunk(
            metadata={
                "source": "pdf",
            }
        )
    ]

    chunker.chunk.return_value = chunks
    enricher.enrich.return_value = enriched_chunks

    error = RuntimeError(
        "Context attachment failed"
    )

    attacher.attach.side_effect = error

    pipeline = DocumentIngestionPipeline(
        document_chunker=chunker,
        metadata_enricher=enricher,
        context_attacher=attacher,
    )

    with pytest.raises(
        RuntimeError,
        match="Context attachment failed",
    ):
        pipeline.process(
            extraction_result,
            context,
        )


# ---------------------------------------------------------------------------
# Input list is not mutated by the pipeline itself
# ---------------------------------------------------------------------------

def test_pipeline_does_not_mutate_input_chunk_list():

    extraction_result = make_extraction_result()
    context = make_context()

    chunker = Mock()
    enricher = Mock()
    attacher = Mock()

    original_chunks = [
        make_final_chunk(
            order_index=0,
            metadata={"source": "pdf"},
        ),
        make_final_chunk(
            order_index=1,
            metadata={"source": "pdf"},
        ),
    ]

    enriched_chunks = [
        make_final_chunk(
            order_index=0,
            metadata={"source": "pdf"},
        ),
        make_final_chunk(
            order_index=1,
            metadata={"source": "pdf"},
        ),
    ]

    final_chunks = [
        make_final_chunk(
            order_index=0,
            metadata={
                "source": "pdf",
                "document_id": 100,
            },
        ),
        make_final_chunk(
            order_index=1,
            metadata={
                "source": "pdf",
                "document_id": 100,
            },
        ),
    ]

    chunker.chunk.return_value = original_chunks
    enricher.enrich.return_value = enriched_chunks
    attacher.attach.return_value = final_chunks

    original_snapshot = list(original_chunks)

    pipeline = DocumentIngestionPipeline(
        document_chunker=chunker,
        metadata_enricher=enricher,
        context_attacher=attacher,
    )

    pipeline.process(
        extraction_result,
        context,
    )

    assert original_chunks == original_snapshot