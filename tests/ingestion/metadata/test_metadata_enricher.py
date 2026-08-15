from app.dto.final_chunk import FinalChunk
from app.dto.extracted_element import ExtractedElement
from app.enums.chunk_type import ChunkType
from app.enums.element_type import ElementType

from app.services.ingestion.metadata.metadata_enricher import (
    MetadataEnricher,
)


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


def make_chunk(
    *,
    text: str = "Hello world",
    elements: list[ExtractedElement] | None = None,
    metadata: dict | None = None,
) -> FinalChunk:
    if elements is None:
        elements = [
            make_element(
                0,
                text,
                metadata={"document_id": 1, "source": "txt"},
            )
        ]

    return FinalChunk(
        text=text,
        elements=elements,
        chunk_type=ChunkType.NARRATIVE,
        section_path=[],
        order_index=elements[0].order_index,
        metadata=metadata or {},
    )


def test_empty_chunks_returns_empty_list():

    enricher = MetadataEnricher()

    result = enricher.enrich([])

    assert result == []


def test_preserves_existing_chunk_metadata():

    chunk = make_chunk(
        metadata={
            "document_id": 10,
            "filename": "report.pdf",
            "source": "docling",
            "page": 4,
        }
    )

    enricher = MetadataEnricher()

    result = enricher.enrich([chunk])

    assert result[0].metadata == {
        "document_id": 10,
        "filename": "report.pdf",
        "source": "docling",
        "page": 4,
    }


def test_falls_back_to_first_element_metadata_when_chunk_metadata_empty():

    element = make_element(
        0,
        "Hello",
        metadata={
            "document_id": 10,
            "filename": "report.pdf",
            "source": "docling",
            "page": 4,
        },
    )

    chunk = make_chunk(
        elements=[element],
        metadata={},
    )

    enricher = MetadataEnricher()

    result = enricher.enrich([chunk])

    assert result[0].metadata == {
        "document_id": 10,
        "filename": "report.pdf",
        "source": "docling",
        "page": 4,
    }


def test_does_not_merge_metadata_from_later_elements():

    first = make_element(
        0,
        "First",
        metadata={
            "document_id": 10,
            "filename": "report.pdf",
            "source": "docling",
            "page": 1,
        },
    )

    second = make_element(
        1,
        "Second",
        metadata={
            "document_id": 10,
            "filename": "report.pdf",
            "source": "docling",
            "page": 2,
        },
    )

    chunk = make_chunk(
        elements=[first, second],
        metadata={},
    )

    enricher = MetadataEnricher()

    result = enricher.enrich([chunk])

    assert result[0].metadata["page"] == 1


def test_does_not_mutate_original_metadata():

    original_metadata = {
        "document_id": 10,
        "filename": "report.pdf",
    }

    chunk = make_chunk(
        metadata=original_metadata,
    )

    enricher = MetadataEnricher()

    result = enricher.enrich([chunk])

    result[0].metadata["new_field"] = "value"

    assert original_metadata == {
        "document_id": 10,
        "filename": "report.pdf",
    }


def test_preserves_chunk_fields():

    element = make_element(
        5,
        "Important content",
        metadata={"source": "docx"},
    )

    chunk = FinalChunk(
        text="Important content",
        elements=[element],
        chunk_type=ChunkType.NARRATIVE,
        section_path=["Chapter 1", "Introduction"],
        order_index=5,
        metadata={},
    )

    enricher = MetadataEnricher()

    result = enricher.enrich([chunk])

    enriched = result[0]

    assert enriched.text == chunk.text
    assert enriched.elements == chunk.elements
    assert enriched.chunk_type == chunk.chunk_type
    assert enriched.section_path == chunk.section_path
    assert enriched.order_index == chunk.order_index

def test_enriches_all_chunks():

    chunk_1 = make_chunk(
        metadata={"document_id": 1}
    )

    chunk_2 = make_chunk(
        metadata={"document_id": 2}
    )

    chunk_3 = make_chunk(
        metadata={"document_id": 3}
    )

    enricher = MetadataEnricher()

    result = enricher.enrich(
        [chunk_1, chunk_2, chunk_3]
    )

    assert len(result) == 3

    assert result[0].metadata["document_id"] == 1
    assert result[1].metadata["document_id"] == 2
    assert result[2].metadata["document_id"] == 3