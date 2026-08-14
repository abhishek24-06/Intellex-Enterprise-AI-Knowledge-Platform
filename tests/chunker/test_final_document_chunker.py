from unittest.mock import Mock

import pytest

from app.dto.chunk_candidate import ChunkCandidate
from app.dto.code_chunk import CodeChunk
from app.dto.extracted_element import ExtractedElement
from app.dto.final_chunk import FinalChunk
from app.dto.routed_chunk import RoutedChunk
from app.dto.table_chunk import TableChunk

from app.enums.chunk_type import ChunkType
from app.enums.element_type import ElementType

from app.services.chunking.final_chunker.document_chunker import DocumentChunker

from app.services.chunking.structure_detection.models import (
    StructureDetectionResult,
    StructureScores,
    StructureType,
)


# ============================================================
# HELPERS
# ============================================================

def make_element(
    order_index: int,
    text: str,
    element_type: ElementType = ElementType.PARAGRAPH,
    metadata: dict | None = None,
) -> ExtractedElement:

    return ExtractedElement(
        order_index=order_index,
        text=text,
        element_type=element_type,
        metadata=metadata or {},
    )


def make_candidate(
    order_index: int,
    text: str,
    elements: list[ExtractedElement] | None = None,
) -> ChunkCandidate:

    if elements is None:
        elements = [
            make_element(
                order_index=order_index,
                text=text,
            )
        ]

    return ChunkCandidate(
        text=text,
        elements=elements,
        heading=None,
        section_path=[],
    )


def make_narrative_routed_chunk(
    candidate: ChunkCandidate,
) -> RoutedChunk:

    return RoutedChunk(
        chunk_type=ChunkType.NARRATIVE,
        elements=candidate.elements,
        text=candidate.text,
        section_path=candidate.section_path,
        order_index=candidate.elements[0].order_index,
    )


def make_table_routed_chunk(
    order_index: int,
    text: str = "table",
) -> RoutedChunk:

    table = make_element(
        order_index=order_index,
        text=text,
        element_type=ElementType.TABLE,
        metadata={
            "cells": [
                ["A", "B"],
                ["1", "2"],
            ],
            "has_header_row": True,
        },
    )

    return RoutedChunk(
        chunk_type=ChunkType.TABLE,
        elements=[table],
        text=None,
        section_path=[],
        order_index=order_index,
    )


def make_code_routed_chunk(
    order_index: int,
    text: str = "print('hello')",
) -> RoutedChunk:

    code = make_element(
        order_index=order_index,
        text=text,
        element_type=ElementType.CODE_BLOCK,
        metadata={
            "language": "python",
        },
    )

    return RoutedChunk(
        chunk_type=ChunkType.CODE,
        elements=[code],
        text=None,
        section_path=[],
        order_index=order_index,
    )


def make_table_chunk(
    text: str,
    elements: list[ExtractedElement],
) -> TableChunk:

    return TableChunk(
        text=text,
        elements=elements,
        metadata={
            "is_table_chunk": True,
        },
    )


def make_code_chunk(
    text: str,
    elements: list[ExtractedElement],
) -> CodeChunk:

    return CodeChunk(
        text=text,
        elements=elements,
        metadata={
            "language": "python",
        },
    )


def make_detector(
    structure_type: StructureType,
) -> Mock:

    detector = Mock()

    if structure_type == StructureType.STRUCTURED:

        detector.detect.return_value = StructureDetectionResult(
            structure_type=StructureType.STRUCTURED,
            confidence=0.9,
            scores=StructureScores(
                structured=0.9,
                unstructured=0.1,
                tabular=0.0,
            ),
        )

    elif structure_type == StructureType.UNSTRUCTURED:

        detector.detect.return_value = StructureDetectionResult(
            structure_type=StructureType.UNSTRUCTURED,
            confidence=0.9,
            scores=StructureScores(
                structured=0.1,
                unstructured=0.9,
                tabular=0.0,
            ),
        )

    elif structure_type == StructureType.TABULAR:

        detector.detect.return_value = StructureDetectionResult(
            structure_type=StructureType.TABULAR,
            confidence=0.9,
            scores=StructureScores(
                structured=0.1,
                unstructured=0.2,
                tabular=0.7,
            ),
        )

    return detector


def make_extraction_result(elements):

    from app.dto.extraction_result import ExtractionResult

    return ExtractionResult(
        elements=elements
    )


def make_document_chunker(
    *,
    detector,
    structure_builder=None,
    hierarchy_chunker=None,
    semantic_chunker=None,
    router=None,
    narrative_splitter=None,
    table_chunker=None,
    code_chunker=None,
    final_chunk_validator=None
):

    return DocumentChunker(
        structure_detector=detector,
        structure_builder=structure_builder or Mock(),
        hierarchy_chunker=hierarchy_chunker or Mock(),
        semantic_chunker=semantic_chunker or Mock(),
        element_router=router or Mock(),
        narrative_safety_splitter=narrative_splitter or Mock(),
        table_chunker=table_chunker or Mock(),
        code_chunker=code_chunker or Mock(),
        final_chunk_validator=final_chunk_validator or Mock()
    )


# ============================================================
# 1. EMPTY DOCUMENT
# ============================================================

def test_empty_document_returns_empty_list():

    detector = Mock()

    extraction_result = make_extraction_result([])

    chunker = make_document_chunker(
        detector=detector,
    )

    result = chunker.chunk(
        extraction_result
    )

    assert result == []

    detector.detect.assert_not_called()


# ============================================================
# 2. DETECTOR IS CALLED EXACTLY ONCE
# ============================================================

def test_detector_called_once():

    element = make_element(
        0,
        "Hello",
    )

    extraction_result = make_extraction_result(
        [element]
    )

    detector = make_detector(
        StructureType.UNSTRUCTURED
    )

    semantic_chunker = Mock()

    candidate = make_candidate(
        0,
        "Hello",
    )

    semantic_chunker.chunk.return_value = [
        candidate
    ]

    router = Mock()

    routed = make_narrative_routed_chunk(
        candidate
    )

    router.route.return_value = [
        routed
    ]

    narrative_splitter = Mock()

    narrative_splitter.split.return_value = [
        routed
    ]

    chunker = make_document_chunker(
        detector=detector,
        semantic_chunker=semantic_chunker,
        router=router,
        narrative_splitter=narrative_splitter,
    )

    chunker.chunk(
        extraction_result
    )

    detector.detect.assert_called_once_with(
        extraction_result
    )


# ============================================================
# 3. STRUCTURED ROUTE
# ============================================================

def test_structured_document_uses_structure_builder_and_hierarchy_chunker():

    element = make_element(
        0,
        "Heading",
        ElementType.HEADING,
    )

    extraction_result = make_extraction_result(
        [element]
    )

    detector = make_detector(
        StructureType.STRUCTURED
    )

    structure_builder = Mock()

    fake_tree = Mock()

    structure_builder.build.return_value = fake_tree

    hierarchy_chunker = Mock()

    candidate = make_candidate(
        0,
        "Structured section",
    )

    hierarchy_chunker.chunk.return_value = [
        candidate
    ]

    router = Mock()

    routed = make_narrative_routed_chunk(
        candidate
    )

    router.route.return_value = [
        routed
    ]

    narrative_splitter = Mock()

    narrative_splitter.split.return_value = [
        routed
    ]

    chunker = make_document_chunker(
        detector=detector,
        structure_builder=structure_builder,
        hierarchy_chunker=hierarchy_chunker,
        router=router,
        narrative_splitter=narrative_splitter,
    )

    result = chunker.chunk(
        extraction_result
    )

    structure_builder.build.assert_called_once_with(
        extraction_result
    )

    hierarchy_chunker.chunk.assert_called_once_with(
        fake_tree
    )

    assert len(result) == 1

    assert result[0].chunk_type == ChunkType.NARRATIVE


# ============================================================
# 4. UNSTRUCTURED ROUTE
# ============================================================

def test_unstructured_document_uses_semantic_chunker():

    element = make_element(
        0,
        "Narrative",
    )

    extraction_result = make_extraction_result(
        [element]
    )

    detector = make_detector(
        StructureType.UNSTRUCTURED
    )

    semantic_chunker = Mock()

    candidate = make_candidate(
        0,
        "Narrative",
    )

    semantic_chunker.chunk.return_value = [
        candidate
    ]

    router = Mock()

    routed = make_narrative_routed_chunk(
        candidate
    )

    router.route.return_value = [
        routed
    ]

    narrative_splitter = Mock()

    narrative_splitter.split.return_value = [
        routed
    ]

    chunker = make_document_chunker(
        detector=detector,
        semantic_chunker=semantic_chunker,
        router=router,
        narrative_splitter=narrative_splitter,
    )

    result = chunker.chunk(
        extraction_result
    )

    semantic_chunker.chunk.assert_called_once_with(
        extraction_result
    )

    assert len(result) == 1


# ============================================================
# 5. TABULAR ROUTE
# ============================================================

def test_tabular_document_creates_candidate_and_routes_it():

    elements = [
        make_element(
            0,
            "Table introduction",
        ),

        make_element(
            1,
            "table content",
            ElementType.TABLE,
            {
                "cells": [
                    ["A", "B"],
                    ["1", "2"],
                ],
                "has_header_row": True,
            },
        ),
    ]

    extraction_result = make_extraction_result(
        elements
    )

    detector = make_detector(
        StructureType.TABULAR
    )

    router = Mock()

    table_route = make_table_routed_chunk(
        order_index=1
    )

    router.route.return_value = [
        table_route
    ]

    table_chunker = Mock()

    table_chunk = make_table_chunk(
        text="A | B\n1 | 2",
        elements=table_route.elements,
    )

    table_chunker.chunk.return_value = [
        table_chunk
    ]

    chunker = make_document_chunker(
        detector=detector,
        router=router,
        table_chunker=table_chunker,
    )

    result = chunker.chunk(
        extraction_result
    )

    router.route.assert_called_once()

    routed_candidate = router.route.call_args.args[0]

    assert routed_candidate.elements == elements

    # Table must NOT appear in candidate.text.
    assert "table content" not in (
        routed_candidate.text or ""
    )

    assert len(result) == 1

    assert result[0].chunk_type == ChunkType.TABLE


# ============================================================
# 6. EVERY CANDIDATE IS ROUTED
# ============================================================

def test_routes_every_chunk_candidate():

    candidate_1 = make_candidate(
        order_index=0,
        text="Section one",
    )

    candidate_2 = make_candidate(
        order_index=10,
        text="Section two",
    )

    detector = make_detector(
        StructureType.STRUCTURED
    )

    hierarchy_chunker = Mock()

    hierarchy_chunker.chunk.return_value = [
        candidate_1,
        candidate_2,
    ]

    router = Mock()

    router.route.side_effect = [
        [
            make_narrative_routed_chunk(
                candidate_1
            )
        ],
        [
            make_narrative_routed_chunk(
                candidate_2
            )
        ],
    ]

    narrative_splitter = Mock()

    narrative_splitter.split.side_effect = (
        lambda routed: [routed]
    )

    chunker = make_document_chunker(
        detector=detector,
        hierarchy_chunker=hierarchy_chunker,
        router=router,
        narrative_splitter=narrative_splitter,
    )

    extraction_result = make_extraction_result(
        [
            make_element(0, "Section one"),
            make_element(10, "Section two"),
        ]
    )

    result = chunker.chunk(
        extraction_result
    )

    assert router.route.call_count == 2

    router.route.assert_any_call(
        candidate_1
    )

    router.route.assert_any_call(
        candidate_2
    )

    assert len(result) == 2


# ============================================================
# 7. NARRATIVE DISPATCH
# ============================================================

def test_narrative_route_uses_safety_splitter():

    candidate = make_candidate(
        0,
        "Narrative",
    )

    routed = make_narrative_routed_chunk(
        candidate
    )

    detector = make_detector(
        StructureType.UNSTRUCTURED
    )

    semantic_chunker = Mock()

    semantic_chunker.chunk.return_value = [
        candidate
    ]

    router = Mock()

    router.route.return_value = [
        routed
    ]

    narrative_splitter = Mock()

    narrative_splitter.split.return_value = [
        routed
    ]

    chunker = make_document_chunker(
        detector=detector,
        semantic_chunker=semantic_chunker,
        router=router,
        narrative_splitter=narrative_splitter,
    )

    result = chunker.chunk(
        make_extraction_result(
            [candidate.elements[0]]
        )
    )

    narrative_splitter.split.assert_called_once_with(
        routed
    )

    assert result[0].chunk_type == ChunkType.NARRATIVE


# ============================================================
# 8. TABLE DISPATCH
# ============================================================

def test_table_route_uses_table_chunker():

    routed = make_table_routed_chunk(
        2
    )

    detector = make_detector(
        StructureType.TABULAR
    )

    router = Mock()

    router.route.return_value = [
        routed
    ]

    table_chunker = Mock()

    table_chunker.chunk.return_value = [
        make_table_chunk(
            "A | B",
            routed.elements,
        )
    ]

    chunker = make_document_chunker(
        detector=detector,
        router=router,
        table_chunker=table_chunker,
    )

    result = chunker.chunk(
        make_extraction_result(
            routed.elements
        )
    )

    table_chunker.chunk.assert_called_once_with(
        routed
    )

    assert result[0].chunk_type == ChunkType.TABLE


# ============================================================
# 9. CODE DISPATCH
# ============================================================

def test_code_route_uses_code_chunker():

    routed = make_code_routed_chunk(
        4
    )

    detector = make_detector(
        StructureType.TABULAR
    )

    router = Mock()

    router.route.return_value = [
        routed
    ]

    code_chunker = Mock()

    code_chunker.chunk.return_value = [
        make_code_chunk(
            routed.elements[0].text,
            routed.elements,
        )
    ]

    chunker = make_document_chunker(
        detector=detector,
        router=router,
        code_chunker=code_chunker,
    )

    result = chunker.chunk(
        make_extraction_result(
            routed.elements
        )
    )

    code_chunker.chunk.assert_called_once_with(
        routed
    )

    assert result[0].chunk_type == ChunkType.CODE


# ============================================================
# 10. MIXED DOCUMENT — CRITICAL ORDERING TEST
# ============================================================

def test_mixed_document_produces_final_chunks_in_document_order():

    elements = [
        make_element(
            0,
            "Paragraph 0",
        ),

        make_element(
            1,
            "Paragraph 1",
        ),

        make_element(
            2,
            "table",
            ElementType.TABLE,
            {
                "cells": [
                    ["A", "B"],
                    ["1", "2"],
                ],
                "has_header_row": True,
            },
        ),

        make_element(
            3,
            "Paragraph 3",
        ),

        make_element(
            4,
            "print('hello')",
            ElementType.CODE_BLOCK,
            {
                "language": "python",
            },
        ),

        make_element(
            5,
            "List item",
            ElementType.LIST,
        ),
    ]

    extraction_result = make_extraction_result(
        elements
    )

    detector = make_detector(
        StructureType.UNSTRUCTURED
    )

    candidate = ChunkCandidate(
        text=(
            "Paragraph 0\n\n"
            "Paragraph 1\n\n"
            "Paragraph 3\n\n"
            "List item"
        ),
        elements=elements,
        heading=None,
        section_path=[],
    )

    semantic_chunker = Mock()

    semantic_chunker.chunk.return_value = [
        candidate
    ]

    router = Mock()

    narrative_route = RoutedChunk(
        chunk_type=ChunkType.NARRATIVE,
        elements=[
            elements[0],
            elements[1],
            elements[3],
            elements[5],
        ],
        text=candidate.text,
        section_path=[],
        order_index=0,
    )

    table_route = RoutedChunk(
        chunk_type=ChunkType.TABLE,
        elements=[elements[2]],
        text=None,
        section_path=[],
        order_index=2,
    )

    code_route = RoutedChunk(
        chunk_type=ChunkType.CODE,
        elements=[elements[4]],
        text=None,
        section_path=[],
        order_index=4,
    )

    router.route.return_value = [
        narrative_route,
        table_route,
        code_route,
    ]

    narrative_splitter = Mock()

    narrative_splitter.split.return_value = [
        narrative_route
    ]

    table_chunker = Mock()

    table_chunker.chunk.return_value = [
        make_table_chunk(
            "A | B\n1 | 2",
            [elements[2]],
        )
    ]

    code_chunker = Mock()

    code_chunker.chunk.return_value = [
        make_code_chunk(
            "print('hello')",
            [elements[4]],
        )
    ]

    chunker = make_document_chunker(
        detector=detector,
        semantic_chunker=semantic_chunker,
        router=router,
        narrative_splitter=narrative_splitter,
        table_chunker=table_chunker,
        code_chunker=code_chunker,
    )

    final_chunks = chunker.chunk(
        extraction_result
    )

    assert [
        chunk.order_index
        for chunk in final_chunks
    ] == [
        0,
        2,
        4,
    ]

    assert [
        chunk.chunk_type
        for chunk in final_chunks
    ] == [
        ChunkType.NARRATIVE,
        ChunkType.TABLE,
        ChunkType.CODE,
    ]


# ============================================================
# 11. MULTI-PIECE TABLE + CODE
# ============================================================

def test_multiple_delegated_pieces_preserve_source_order_index():

    table_element = make_element(
        1,
        "table",
        ElementType.TABLE,
        {
            "cells": [
                ["A", "B"],
                ["1", "2"],
            ],
            "has_header_row": True,
        },
    )

    code_element = make_element(
        3,
        "def test():\n    return True",
        ElementType.CODE_BLOCK,
        {
            "language": "python",
        },
    )

    narrative_element_0 = make_element(
        0,
        "Paragraph 0",
    )

    narrative_element_2 = make_element(
        2,
        "Paragraph 2",
    )

    elements = [
        narrative_element_0,
        table_element,
        narrative_element_2,
        code_element,
    ]

    extraction_result = make_extraction_result(
        elements
    )

    detector = make_detector(
        StructureType.UNSTRUCTURED
    )

    candidate = ChunkCandidate(
        text=(
            "Paragraph 0\n\n"
            "Paragraph 2"
        ),
        elements=elements,
        heading=None,
        section_path=[],
    )

    semantic_chunker = Mock()

    semantic_chunker.chunk.return_value = [
        candidate
    ]

    router = Mock()

    narrative_route = RoutedChunk(
        chunk_type=ChunkType.NARRATIVE,
        elements=[
            narrative_element_0,
            narrative_element_2,
        ],
        text=candidate.text,
        section_path=[],
        order_index=0,
    )

    table_route = make_table_routed_chunk(
        1
    )

    code_route = make_code_routed_chunk(
        3,
        code_element.text,
    )

    router.route.return_value = [
        narrative_route,
        table_route,
        code_route,
    ]

    narrative_splitter = Mock()

    narrative_splitter.split.return_value = [
        narrative_route
    ]

    table_chunker = Mock()

    table_chunker.chunk.return_value = [
        make_table_chunk(
            "table part 1",
            [table_element],
        ),
        make_table_chunk(
            "table part 2",
            [table_element],
        ),
        make_table_chunk(
            "table part 3",
            [table_element],
        ),
    ]

    code_chunker = Mock()

    code_chunker.chunk.return_value = [
        make_code_chunk(
            "code part 1",
            [code_element],
        ),
        make_code_chunk(
            "code part 2",
            [code_element],
        ),
    ]

    chunker = make_document_chunker(
        detector=detector,
        semantic_chunker=semantic_chunker,
        router=router,
        narrative_splitter=narrative_splitter,
        table_chunker=table_chunker,
        code_chunker=code_chunker,
    )

    final_chunks = chunker.chunk(
        extraction_result
    )

    assert [
        chunk.order_index
        for chunk in final_chunks
    ] == [
        0,
        1,
        1,
        1,
        3,
        3,
    ]

    assert [
        chunk.chunk_type
        for chunk in final_chunks
    ] == [
        ChunkType.NARRATIVE,
        ChunkType.TABLE,
        ChunkType.TABLE,
        ChunkType.TABLE,
        ChunkType.CODE,
        ChunkType.CODE,
    ]


# ============================================================
# 12. SPECIALIZED CHUNK METADATA IS PRESERVED
# ============================================================

def test_specialized_metadata_is_preserved():

    routed = make_code_routed_chunk(
        10
    )

    detector = make_detector(
        StructureType.TABULAR
    )

    router = Mock()

    router.route.return_value = [
        routed
    ]

    code_chunker = Mock()

    code_chunker.chunk.return_value = [
        CodeChunk(
            text="print('hello')",
            elements=routed.elements,
            metadata={
                "language": "python",
                "custom": "value",
            },
        )
    ]

    chunker = make_document_chunker(
        detector=detector,
        router=router,
        code_chunker=code_chunker,
    )

    result = chunker.chunk(
        make_extraction_result(
            routed.elements
        )
    )

    assert result[0].metadata == {
        "language": "python",
        "custom": "value",
    }


# ============================================================
# 13. SECTION PATH IS PRESERVED
# ============================================================

def test_section_path_is_preserved():

    element = make_element(
        10,
        "Narrative",
    )

    candidate = ChunkCandidate(
        text="Narrative",
        elements=[element],
        heading=None,
        section_path=[
            "Architecture",
            "Retrieval",
        ],
    )

    routed = RoutedChunk(
        chunk_type=ChunkType.NARRATIVE,
        elements=[element],
        text="Narrative",
        section_path=[
            "Architecture",
            "Retrieval",
        ],
        order_index=10,
    )

    detector = make_detector(
        StructureType.UNSTRUCTURED
    )

    semantic_chunker = Mock()

    semantic_chunker.chunk.return_value = [
        candidate
    ]

    router = Mock()

    router.route.return_value = [
        routed
    ]

    narrative_splitter = Mock()

    narrative_splitter.split.return_value = [
        routed
    ]

    chunker = make_document_chunker(
        detector=detector,
        semantic_chunker=semantic_chunker,
        router=router,
        narrative_splitter=narrative_splitter,
    )

    result = chunker.chunk(
        make_extraction_result(
            [element]
        )
    )

    assert result[0].section_path == [
        "Architecture",
        "Retrieval",
    ]


# ============================================================
# 14. NO DUPLICATION OF SOURCE ELEMENTS
# ============================================================

def test_mixed_document_does_not_duplicate_source_elements():

    elements = [
        make_element(
            0,
            "Paragraph",
        ),

        make_element(
            1,
            "Table",
            ElementType.TABLE,
            {
                "cells": [
                    ["A"],
                    ["1"],
                ],
                "has_header_row": True,
            },
        ),

        make_element(
            2,
            "Code",
            ElementType.CODE_BLOCK,
            {
                "language": "python",
            },
        ),
    ]

    extraction_result = make_extraction_result(
        elements
    )

    detector = make_detector(
        StructureType.UNSTRUCTURED
    )

    candidate = ChunkCandidate(
        text="Paragraph",
        elements=elements,
        heading=None,
        section_path=[],
    )

    semantic_chunker = Mock()

    semantic_chunker.chunk.return_value = [
        candidate
    ]

    router = Mock()

    narrative_route = RoutedChunk(
        chunk_type=ChunkType.NARRATIVE,
        elements=[elements[0]],
        text="Paragraph",
        section_path=[],
        order_index=0,
    )

    table_route = make_table_routed_chunk(
        1
    )

    code_route = make_code_routed_chunk(
        2
    )

    router.route.return_value = [
        narrative_route,
        table_route,
        code_route,
    ]

    narrative_splitter = Mock()

    narrative_splitter.split.return_value = [
        narrative_route
    ]

    table_chunker = Mock()

    table_chunker.chunk.return_value = [
        make_table_chunk(
            "table",
            [elements[1]],
        )
    ]

    code_chunker = Mock()

    code_chunker.chunk.return_value = [
        make_code_chunk(
            "code",
            [elements[2]],
        )
    ]

    chunker = make_document_chunker(
        detector=detector,
        semantic_chunker=semantic_chunker,
        router=router,
        narrative_splitter=narrative_splitter,
        table_chunker=table_chunker,
        code_chunker=code_chunker,
    )

    final_chunks = chunker.chunk(
        extraction_result
    )

    flattened = [
        element.order_index
        for chunk in final_chunks
        for element in chunk.elements
    ]

    assert sorted(flattened) == [
        0,
        1,
        2,
    ]


# ============================================================
# 15. UNSUPPORTED STRUCTURE TYPE
# ============================================================

def test_unsupported_structure_type_raises():

    element = make_element(
        0,
        "Something",
    )

    extraction_result = make_extraction_result(
        [element]
    )

    detector = Mock()

    detector.detect.return_value = Mock(
        structure_type="INVALID"
    )

    chunker = make_document_chunker(
        detector=detector,
    )

    with pytest.raises(
        ValueError,
        match="Unsupported structure type",
    ):
        chunker.chunk(
            extraction_result
        )


# ============================================================
# 16. FINAL CHUNKS ARE SORTED
# ============================================================

def test_final_chunks_are_sorted_by_order_index():

    candidate = make_candidate(
        0,
        "Narrative",
    )

    detector = make_detector(
        StructureType.UNSTRUCTURED
    )

    semantic_chunker = Mock()

    semantic_chunker.chunk.return_value = [
        candidate
    ]

    router = Mock()

    route_10 = make_narrative_routed_chunk(
        make_candidate(
            10,
            "Later",
        )
    )

    route_2 = make_table_routed_chunk(
        2
    )

    route_5 = make_code_routed_chunk(
        5
    )

    # Deliberately return them out of order.
    router.route.return_value = [
        route_10,
        route_2,
        route_5,
    ]

    narrative_splitter = Mock()

    narrative_splitter.split.return_value = [
        route_10
    ]

    table_chunker = Mock()

    table_chunker.chunk.return_value = [
        make_table_chunk(
            "table",
            route_2.elements,
        )
    ]

    code_chunker = Mock()

    code_chunker.chunk.return_value = [
        make_code_chunk(
            "code",
            route_5.elements,
        )
    ]

    chunker = make_document_chunker(
        detector=detector,
        semantic_chunker=semantic_chunker,
        router=router,
        narrative_splitter=narrative_splitter,
        table_chunker=table_chunker,
        code_chunker=code_chunker,
    )

    result = chunker.chunk(
        make_extraction_result(
            [candidate.elements[0]]
        )
    )

    assert [
        chunk.order_index
        for chunk in result
    ] == [
        2,
        5,
        10,
    ]


# ============================================================
# 17. SPECIALIZED CHUNKS GET SOURCE ORDER INDEX
# ============================================================

def test_specialized_chunks_inherit_source_order_index():

    routed = make_code_routed_chunk(
        25
    )

    detector = make_detector(
        StructureType.TABULAR
    )

    router = Mock()

    router.route.return_value = [
        routed
    ]

    code_chunker = Mock()

    code_chunker.chunk.return_value = [
        make_code_chunk(
            "part 1",
            routed.elements,
        ),
        make_code_chunk(
            "part 2",
            routed.elements,
        ),
    ]

    chunker = make_document_chunker(
        detector=detector,
        router=router,
        code_chunker=code_chunker,
    )

    result = chunker.chunk(
        make_extraction_result(
            routed.elements
        )
    )

    assert [
        chunk.order_index
        for chunk in result
    ] == [
        25,
        25,
    ]


# ============================================================
# 18. FINAL OUTPUT IS ACTUALLY FinalChunk
# ============================================================

def test_final_output_contains_only_final_chunk_objects():

    routed = make_code_routed_chunk(
        5
    )

    detector = make_detector(
        StructureType.TABULAR
    )

    router = Mock()

    router.route.return_value = [
        routed
    ]

    code_chunker = Mock()

    code_chunker.chunk.return_value = [
        make_code_chunk(
            "print('hello')",
            routed.elements,
        )
    ]

    chunker = make_document_chunker(
        detector=detector,
        router=router,
        code_chunker=code_chunker,
    )

    result = chunker.chunk(
        make_extraction_result(
            routed.elements
        )
    )

    assert all(
        isinstance(chunk, FinalChunk)
        for chunk in result
    )

def test_tabular_candidate_excludes_all_table_text():
    
    table_1 = make_element(
        0,
        "TABLE_ONE_CONTENT",
        ElementType.TABLE,
    )

    paragraph = make_element(
        1,
        "Important explanation",
    )

    table_2 = make_element(
        2,
        "TABLE_TWO_CONTENT",
        ElementType.TABLE,
    )

    extraction_result = make_extraction_result(
        [
            table_1,
            paragraph,
            table_2,
        ]
    )

    detector = make_detector(
        StructureType.TABULAR
    )

    router = Mock()

    routed = make_narrative_routed_chunk(
        make_candidate(
            1,
            "Important explanation",
            [table_1, paragraph, table_2],
        )
    )

    router.route.return_value = [
        routed
    ]

    narrative_splitter = Mock()
    narrative_splitter.split.return_value = []

    chunker = make_document_chunker(
        detector=detector,
        router=router,
        narrative_splitter=narrative_splitter
    )

    chunker.chunk(
        extraction_result
    )

    router.route.assert_called_once()

    candidate = router.route.call_args.args[0]

    # Narrative text contains only narrative content.
    assert candidate.text == "Important explanation"

    assert "TABLE_ONE_CONTENT" not in candidate.text
    assert "TABLE_TWO_CONTENT" not in candidate.text

    # But ALL source elements remain attached.
    assert candidate.elements == [
        table_1,
        paragraph,
        table_2,
    ]

def test_narrative_metadata_is_preserved_from_first_source_element():
    metadata = {
        "document_id": "doc-123",
        "filename": "report.pdf",
        "page": 4,
        "source": "docling",
    }

    element_0 = make_element(
        order_index=0,
        text="First paragraph",
        metadata=metadata,
    )

    element_1 = make_element(
        order_index=1,
        text="Second paragraph",
        metadata={
            "document_id": "doc-123",
            "filename": "report.pdf",
            "page": 5,
            "source": "docling",
        },
    )

    candidate = ChunkCandidate(
        text="First paragraph\n\nSecond paragraph",
        elements=[element_0, element_1],
        heading=None,
        section_path=[],
    )

    routed = RoutedChunk(
        chunk_type=ChunkType.NARRATIVE,
        elements=[element_0, element_1],
        text=candidate.text,
        section_path=[],
        order_index=0,
    )

    detector = make_detector(
        StructureType.UNSTRUCTURED
    )

    semantic_chunker = Mock()
    semantic_chunker.chunk.return_value = [candidate]

    router = Mock()
    router.route.return_value = [routed]

    narrative_splitter = Mock()
    narrative_splitter.split.return_value = [routed]

    final_chunk_validator = Mock()

    chunker = make_document_chunker(
        detector=detector,
        semantic_chunker=semantic_chunker,
        router=router,
        narrative_splitter=narrative_splitter,
        final_chunk_validator=final_chunk_validator,
    )

    result = chunker.chunk(
        make_extraction_result(
            [element_0, element_1]
        )
    )

    assert len(result) == 1

    assert result[0].metadata == metadata