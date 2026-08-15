from unittest.mock import Mock

from app.dto.chunk_candidate import ChunkCandidate
from app.dto.extracted_element import ExtractedElement
from app.dto.extraction_result import ExtractionResult
from app.dto.final_chunk import FinalChunk
from app.dto.routed_chunk import RoutedChunk

from app.enums.chunk_type import ChunkType
from app.enums.element_type import ElementType

from app.services.chunking.final_chunker.document_chunker import DocumentChunker
from app.services.chunking.structure_detection.models import StructureType

def make_paragraph(order_index: int, text: str):
    return ExtractedElement(
        order_index=order_index,
        text=text,
        element_type=ElementType.PARAGRAPH,
        metadata={},
    )


def make_table(order_index: int):
    return ExtractedElement(
        order_index=order_index,
        text="A | B\n1 | 2",
        element_type=ElementType.TABLE,
        metadata={
            "cells": [
                ["A", "B"],
                ["1", "2"],
            ],
            "has_header_row": True,
        },
    )


def make_code(order_index: int, text: str):
    return ExtractedElement(
        order_index=order_index,
        text=text,
        element_type=ElementType.CODE_BLOCK,
        metadata={
            "language": "python",
        },
    )


def make_result(elements):
    return ExtractionResult(elements=elements)

def test_multiple_candidates_are_all_routed_and_processed():

    elements = [
        make_paragraph(0, "First section"),
        make_paragraph(1, "Second section"),
    ]

    extraction_result = make_result(elements)

    detector = Mock()
    detector.detect.return_value = Mock(
        structure_type=StructureType.UNSTRUCTURED
    )

    candidate_1 = ChunkCandidate(
        text="First section",
        elements=[elements[0]],
        heading=None,
        section_path=["Section 1"],
    )

    candidate_2 = ChunkCandidate(
        text="Second section",
        elements=[elements[1]],
        heading=None,
        section_path=["Section 2"],
    )

    semantic_chunker = Mock()
    semantic_chunker.chunk.return_value = [
        candidate_1,
        candidate_2,
    ]

    router = Mock()

    route_1 = RoutedChunk(
        chunk_type=ChunkType.NARRATIVE,
        elements=[elements[0]],
        text="First section",
        section_path=["Section 1"],
        order_index=0,
    )

    route_2 = RoutedChunk(
        chunk_type=ChunkType.NARRATIVE,
        elements=[elements[1]],
        text="Second section",
        section_path=["Section 2"],
        order_index=1,
    )

    router.route.side_effect = [
        [route_1],
        [route_2],
    ]

    narrative_splitter = Mock()
    narrative_splitter.split.side_effect = [
        [route_1],
        [route_2],
    ]

    chunker = DocumentChunker(
        structure_detector=detector,
        structure_builder=Mock(),
        hierarchy_chunker=Mock(),
        semantic_chunker=semantic_chunker,
        element_router=router,
        narrative_safety_splitter=narrative_splitter,
        table_chunker=Mock(),
        code_chunker=Mock(),
        final_chunk_validator=Mock(),
    )

    final_chunks = chunker.chunk(extraction_result)

    assert router.route.call_count == 2

    assert [
        chunk.order_index
        for chunk in final_chunks
    ] == [0, 1]

def test_mixed_document_preserves_order_when_specialized_chunks_split():

    paragraph_0 = make_paragraph(
        0,
        "Narrative before table",
    )

    table = make_table(1)

    code = make_code(
        2,
        "def hello():\n    return True",
    )

    paragraph_3 = make_paragraph(
        3,
        "Narrative after code",
    )

    elements = [
        paragraph_0,
        table,
        code,
        paragraph_3,
    ]

    extraction_result = make_result(elements)

    detector = Mock()
    detector.detect.return_value = Mock(
        structure_type=StructureType.UNSTRUCTURED
    )

    candidate = ChunkCandidate(
        text=(
            "Narrative before table\n\n"
            "Narrative after code"
        ),
        elements=elements,
        heading=None,
        section_path=["Architecture"],
    )

    semantic_chunker = Mock()
    semantic_chunker.chunk.return_value = [candidate]

    router = Mock()

    narrative_route = RoutedChunk(
        chunk_type=ChunkType.NARRATIVE,
        elements=[paragraph_0, paragraph_3],
        text=candidate.text,
        section_path=["Architecture"],
        order_index=0,
    )

    table_route = RoutedChunk(
        chunk_type=ChunkType.TABLE,
        elements=[table],
        text=None,
        section_path=["Architecture"],
        order_index=1,
    )

    code_route = RoutedChunk(
        chunk_type=ChunkType.CODE,
        elements=[code],
        text=None,
        section_path=["Architecture"],
        order_index=2,
    )

    router.route.return_value = [
        narrative_route,
        table_route,
        code_route,
    ]

    narrative_splitter = Mock()
    narrative_splitter.split.return_value = [
        narrative_route,
    ]

    table_piece_1 = Mock(
        text="A | B\n1 | 2",
        elements=[table],
        metadata={"table_index": 0},
    )

    table_piece_2 = Mock(
        text="A | B\n3 | 4",
        elements=[table],
        metadata={"table_index": 1},
    )

    table_chunker = Mock()
    table_chunker.chunk.return_value = [
        table_piece_1,
        table_piece_2,
    ]

    code_piece_1 = Mock(
        text="def hello():",
        elements=[code],
        metadata={"language": "python"},
    )

    code_piece_2 = Mock(
        text="    return True",
        elements=[code],
        metadata={"language": "python"},
    )

    code_chunker = Mock()
    code_chunker.chunk.return_value = [
        code_piece_1,
        code_piece_2,
    ]

    chunker = DocumentChunker(
        structure_detector=detector,
        structure_builder=Mock(),
        hierarchy_chunker=Mock(),
        semantic_chunker=semantic_chunker,
        element_router=router,
        narrative_safety_splitter=narrative_splitter,
        table_chunker=table_chunker,
        code_chunker=code_chunker,
        final_chunk_validator=Mock(),
    )

    final_chunks = chunker.chunk(extraction_result)

    assert [
        chunk.order_index
        for chunk in final_chunks
    ] == [0, 1, 1, 2, 2]

    assert [
        chunk.chunk_type
        for chunk in final_chunks
    ] == [
        ChunkType.NARRATIVE,
        ChunkType.TABLE,
        ChunkType.TABLE,
        ChunkType.CODE,
        ChunkType.CODE,
    ]

    for chunk in final_chunks:
        assert chunk.order_index == min(
            element.order_index
            for element in chunk.elements
        )

def test_empty_extraction_returns_no_chunks():

    extraction_result = ExtractionResult(
        elements=[]
    )

    detector = Mock()

    chunker = DocumentChunker(
        structure_detector=detector,
        structure_builder=Mock(),
        hierarchy_chunker=Mock(),
        semantic_chunker=Mock(),
        element_router=Mock(),
        narrative_safety_splitter=Mock(),
        table_chunker=Mock(),
        code_chunker=Mock(),
        final_chunk_validator=Mock(),
    )

    result = chunker.chunk(extraction_result)

    assert result == []

    detector.detect.assert_not_called()

def test_single_paragraph_produces_one_narrative_chunk():

    element = make_paragraph(
        0,
        "Intellex is an enterprise knowledge platform.",
    )

    extraction_result = make_result([element])

    detector = Mock()
    detector.detect.return_value = Mock(
        structure_type=StructureType.UNSTRUCTURED
    )

    candidate = ChunkCandidate(
        text=element.text,
        elements=[element],
        heading=None,
        section_path=[],
    )

    semantic_chunker = Mock()
    semantic_chunker.chunk.return_value = [candidate]

    route = RoutedChunk(
        chunk_type=ChunkType.NARRATIVE,
        elements=[element],
        text=element.text,
        section_path=[],
        order_index=0,
    )

    router = Mock()
    router.route.return_value = [route]

    splitter = Mock()
    splitter.split.return_value = [route]

    chunker = DocumentChunker(
        structure_detector=detector,
        structure_builder=Mock(),
        hierarchy_chunker=Mock(),
        semantic_chunker=semantic_chunker,
        element_router=router,
        narrative_safety_splitter=splitter,
        table_chunker=Mock(),
        code_chunker=Mock(),
        final_chunk_validator=Mock(),
    )

    chunks = chunker.chunk(extraction_result)

    assert len(chunks) == 1
    assert chunks[0].chunk_type == ChunkType.NARRATIVE
    assert chunks[0].order_index == 0
    assert chunks[0].elements == [element]

def test_single_table_reaches_table_chunker():

    table = make_table(0)

    extraction_result = make_result([table])

    detector = Mock()
    detector.detect.return_value = Mock(
        structure_type=StructureType.TABULAR
    )

    router = Mock()

    route = RoutedChunk(
        chunk_type=ChunkType.TABLE,
        elements=[table],
        text=None,
        section_path=[],
        order_index=0,
    )

    router.route.return_value = [route]

    table_piece = Mock(
        text="A | B\n1 | 2",
        elements=[table],
        metadata={
            "has_header_row": True,
        },
    )

    table_chunker = Mock()
    table_chunker.chunk.return_value = [table_piece]

    chunker = DocumentChunker(
        structure_detector=detector,
        structure_builder=Mock(),
        hierarchy_chunker=Mock(),
        semantic_chunker=Mock(),
        element_router=router,
        narrative_safety_splitter=Mock(),
        table_chunker=table_chunker,
        code_chunker=Mock(),
        final_chunk_validator=Mock(),
    )

    chunks = chunker.chunk(extraction_result)

    assert len(chunks) == 1
    assert chunks[0].chunk_type == ChunkType.TABLE
    assert chunks[0].order_index == 0

    table_chunker.chunk.assert_called_once_with(route)

def test_single_code_block_reaches_code_chunker():

    code = make_code(
        0,
        "print('hello')",
    )

    extraction_result = make_result([code])

    detector = Mock()
    detector.detect.return_value = Mock(
        structure_type=StructureType.UNSTRUCTURED
    )

    candidate = ChunkCandidate(
        text="",
        elements=[code],
        heading=None,
        section_path=[],
    )

    semantic_chunker = Mock()
    semantic_chunker.chunk.return_value = [candidate]

    route = RoutedChunk(
        chunk_type=ChunkType.CODE,
        elements=[code],
        text=None,
        section_path=[],
        order_index=0,
    )

    router = Mock()
    router.route.return_value = [route]

    code_piece = Mock(
        text="print('hello')",
        elements=[code],
        metadata={
            "language": "python",
        },
    )

    code_chunker = Mock()
    code_chunker.chunk.return_value = [code_piece]

    chunker = DocumentChunker(
        structure_detector=detector,
        structure_builder=Mock(),
        hierarchy_chunker=Mock(),
        semantic_chunker=semantic_chunker,
        element_router=router,
        narrative_safety_splitter=Mock(),
        table_chunker=Mock(),
        code_chunker=code_chunker,
        final_chunk_validator=Mock(),
    )

    chunks = chunker.chunk(extraction_result)

    assert len(chunks) == 1
    assert chunks[0].chunk_type == ChunkType.CODE
    assert chunks[0].order_index == 0
    assert chunks[0].metadata["language"] == "python"

def test_structured_document_processes_all_hierarchy_candidates():

    elements = [
        make_paragraph(
            0,
            "Introduction to Intellex",
        ),
        make_paragraph(
            1,
            "Intellex is an enterprise knowledge platform.",
        ),
        make_paragraph(
            2,
            "RAG Pipeline",
        ),
        make_paragraph(
            3,
            "Intellex uses hybrid retrieval.",
        ),
    ]

    extraction_result = make_result(elements)

    # ---------------------------------------------------------
    # Structure detection
    # ---------------------------------------------------------

    detector = Mock()

    detector.detect.return_value = Mock(
        structure_type=StructureType.STRUCTURED
    )

    # ---------------------------------------------------------
    # Structure builder
    # ---------------------------------------------------------

    structure_builder = Mock()

    structure_tree = Mock()

    structure_builder.build.return_value = structure_tree

    # ---------------------------------------------------------
    # Hierarchy chunker returns MULTIPLE candidates
    # ---------------------------------------------------------

    candidate_1 = ChunkCandidate(
        text="Intellex is an enterprise knowledge platform.",
        elements=[elements[1]],
        heading="Introduction to Intellex",
        section_path=["Introduction to Intellex"],
    )

    candidate_2 = ChunkCandidate(
        text="Intellex uses hybrid retrieval.",
        elements=[elements[3]],
        heading="RAG Pipeline",
        section_path=[
            "Introduction to Intellex",
            "RAG Pipeline",
        ],
    )

    hierarchy_chunker = Mock()

    hierarchy_chunker.chunk.return_value = [
        candidate_1,
        candidate_2,
    ]

    # ---------------------------------------------------------
    # ElementRouter
    # ---------------------------------------------------------

    route_1 = RoutedChunk(
        chunk_type=ChunkType.NARRATIVE,
        elements=[elements[1]],
        text=candidate_1.text,
        section_path=candidate_1.section_path,
        order_index=1,
    )

    route_2 = RoutedChunk(
        chunk_type=ChunkType.NARRATIVE,
        elements=[elements[3]],
        text=candidate_2.text,
        section_path=candidate_2.section_path,
        order_index=3,
    )

    router = Mock()

    router.route.side_effect = [
        [route_1],
        [route_2],
    ]

    # ---------------------------------------------------------
    # Narrative safety splitter
    # ---------------------------------------------------------

    narrative_splitter = Mock()

    narrative_splitter.split.side_effect = [
        [route_1],
        [route_2],
    ]

    # ---------------------------------------------------------
    # DocumentChunker
    # ---------------------------------------------------------

    chunker = DocumentChunker(
        structure_detector=detector,
        structure_builder=structure_builder,
        hierarchy_chunker=hierarchy_chunker,
        semantic_chunker=Mock(),
        element_router=router,
        narrative_safety_splitter=narrative_splitter,
        table_chunker=Mock(),
        code_chunker=Mock(),
        final_chunk_validator=Mock(),
    )

    # ---------------------------------------------------------
    # Execute
    # ---------------------------------------------------------

    final_chunks = chunker.chunk(
        extraction_result
    )

    # ---------------------------------------------------------
    # Verify STRUCTURED path
    # ---------------------------------------------------------

    detector.detect.assert_called_once_with(
        extraction_result
    )

    structure_builder.build.assert_called_once_with(
        extraction_result
    )

    hierarchy_chunker.chunk.assert_called_once_with(
        structure_tree
    )

    # ---------------------------------------------------------
    # Critical assertion:
    # BOTH hierarchy candidates reached ElementRouter
    # ---------------------------------------------------------

    assert router.route.call_count == 2

    router.route.assert_any_call(candidate_1)
    router.route.assert_any_call(candidate_2)

    # ---------------------------------------------------------
    # Verify final output
    # ---------------------------------------------------------

    assert len(final_chunks) == 2

    assert [
        chunk.order_index
        for chunk in final_chunks
    ] == [
        1,
        3,
    ]

    assert [
        chunk.chunk_type
        for chunk in final_chunks
    ] == [
        ChunkType.NARRATIVE,
        ChunkType.NARRATIVE,
    ]

    assert final_chunks[0].section_path == [
        "Introduction to Intellex"
    ]

    assert final_chunks[1].section_path == [
        "Introduction to Intellex",
        "RAG Pipeline",
    ]