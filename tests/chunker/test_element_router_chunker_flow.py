from app.dto.chunk_candidate import ChunkCandidate
from app.dto.extracted_element import ExtractedElement
from app.enums.chunk_type import ChunkType
from app.enums.element_type import ElementType
from app.services.chunking.recursive_splitter.narrative_safety_splitter import NarrativeSafetySplitter
from app.services.chunking.routing.element_router import ElementRouter

from app.services.chunking.code.code_chunker import CodeChunker
from app.services.chunking.table.table_chunker import TableChunker


# ============================================================
# HELPERS
# ============================================================

def make_paragraph(
    order_index: int,
    text: str,
) -> ExtractedElement:

    return ExtractedElement(
        order_index=order_index,
        text=text,
        element_type=ElementType.PARAGRAPH,
        metadata={},
    )


def make_code(
    order_index: int,
    code: str,
    language: str = "python",
) -> ExtractedElement:

    return ExtractedElement(
        order_index=order_index,
        text=code,
        element_type=ElementType.CODE_BLOCK,
        metadata={
            "language": language,
        },
    )


def make_table(
    order_index: int,
) -> ExtractedElement:

    cells = [
        ["Component", "Responsibility"],
        ["Retriever", "Finds relevant documents"],
        ["Generator", "Generates the final answer"],
        ["Database", "Stores document metadata"],
    ]

    return ExtractedElement(
        order_index=order_index,
        text="",
        element_type=ElementType.TABLE,
        metadata={
            "cells": cells,
            "has_header_row": True,
        },
    )


def make_candidate(elements):

    elements = sorted(
        elements,
        key=lambda element: element.order_index,
    )

    narrative_elements = [
        element
        for element in elements
        if element.element_type
        not in {
            ElementType.TABLE,
            ElementType.CODE_BLOCK,
        }
    ]

    text = "\n\n".join(
        element.text
        for element in narrative_elements
        if element.text.strip()
    )

    return ChunkCandidate(
        text=text,
        elements=elements,
        heading=None,
        section_path=["Intellex", "Architecture"],
    )


# ============================================================
# 1. ROUTER CREATES THE CORRECT ROUTED CHUNKS
# ============================================================

def test_router_creates_correct_routes():

    elements = [
        make_paragraph(
            0,
            "Intellex uses retrieval augmented generation.",
        ),

        make_paragraph(
            1,
            "The retrieval system searches the knowledge base.",
        ),

        make_table(2),

        make_code(
            3,
            (
                "def retrieve_documents(query):\n"
                "    return search(query)\n"
            ),
        ),

        make_paragraph(
            4,
            "The retrieved documents are passed to the generator.",
        ),
    ]

    candidate = make_candidate(elements)

    router = ElementRouter()

    routed_chunks = router.route(candidate)

    assert len(routed_chunks) == 3

    chunk_types = [
        chunk.chunk_type
        for chunk in routed_chunks
    ]

    assert chunk_types == [
        ChunkType.NARRATIVE,
        ChunkType.TABLE,
        ChunkType.CODE,
    ]


# ============================================================
# 2. NARRATIVE ROUTE
# ============================================================

def test_narrative_route_contains_only_narrative_elements():

    elements = [
        make_paragraph(
            0,
            "Paragraph zero.",
        ),

        make_paragraph(
            1,
            "Paragraph one.",
        ),

        make_table(2),

        make_code(
            3,
            "def test():\n    return True",
        ),

        make_paragraph(
            4,
            "Paragraph four.",
        ),
    ]

    candidate = make_candidate(elements)

    router = ElementRouter()

    routed_chunks = router.route(candidate)

    narrative = next(
        chunk
        for chunk in routed_chunks
        if chunk.chunk_type == ChunkType.NARRATIVE
    )

    assert [
        element.order_index
        for element in narrative.elements
    ] == [0, 1, 4]

    assert all(
        element.element_type
        not in {
            ElementType.TABLE,
            ElementType.CODE_BLOCK,
        }
        for element in narrative.elements
    )


# ============================================================
# 3. TABLE ROUTE
# ============================================================

def test_table_route_contains_only_table():

    table = make_table(2)

    candidate = make_candidate(
        [
            make_paragraph(0, "Narrative"),
            table,
        ]
    )

    router = ElementRouter()

    routed_chunks = router.route(candidate)

    table_route = next(
        chunk
        for chunk in routed_chunks
        if chunk.chunk_type == ChunkType.TABLE
    )

    assert table_route.elements == [table]

    assert table_route.text is None

    assert table_route.order_index == 2


# ============================================================
# 4. CODE ROUTE
# ============================================================

def test_code_route_contains_only_code():

    code = make_code(
        5,
        (
            "def hello():\n"
            "    return 'hello'\n"
        ),
    )

    candidate = make_candidate(
        [
            make_paragraph(0, "Narrative"),
            code,
        ]
    )

    router = ElementRouter()

    routed_chunks = router.route(candidate)

    code_route = next(
        chunk
        for chunk in routed_chunks
        if chunk.chunk_type == ChunkType.CODE
    )

    assert code_route.elements == [code]

    assert code_route.text is None

    assert code_route.order_index == 5


# ============================================================
# 5. ROUTER → NARRATIVE SAFETY SPLITTER
# ============================================================

def test_router_to_narrative_safety_splitter():

    elements = [
        make_paragraph(
            0,
            "A" * 100,
        ),

        make_paragraph(
            1,
            "B" * 100,
        ),

        make_paragraph(
            2,
            "C" * 100,
        ),
    ]

    candidate = make_candidate(elements)

    router = ElementRouter()

    routed_chunks = router.route(candidate)

    narrative_route = next(
        chunk
        for chunk in routed_chunks
        if chunk.chunk_type == ChunkType.NARRATIVE
    )

    splitter = NarrativeSafetySplitter(
        max_tokens=50,
    )

    chunks = splitter.split(
        narrative_route
    )

    assert len(chunks) > 1

    flattened_ids = [
        element.order_index
        for chunk in chunks
        for element in chunk.elements
    ]

    assert flattened_ids == [0, 1, 2]

    assert len(flattened_ids) == len(
        set(flattened_ids)
    )


# ============================================================
# 6. ROUTER → CODE CHUNKER
# ============================================================

def test_router_to_code_chunker():

    code = make_code(
        3,
        (
            "def retrieve(query):\n"
            "    result = search(query)\n"
            "    return result\n"
        ),
        language="python",
    )

    candidate = make_candidate(
        [
            make_paragraph(
                0,
                "The system retrieves documents.",
            ),
            code,
        ]
    )

    router = ElementRouter()

    routed_chunks = router.route(candidate)

    code_route = next(
        chunk
        for chunk in routed_chunks
        if chunk.chunk_type == ChunkType.CODE
    )

    chunker = CodeChunker(
        max_tokens=1000,
    )

    code_chunks = chunker.chunk(
        code_route
    )

    assert len(code_chunks) >= 1

    assert all(
        chunk.elements == [code]
        for chunk in code_chunks
    )

    assert all(
        chunk.metadata["language"] == "python"
        for chunk in code_chunks
    )

    reconstructed = "".join(
        chunk.text
        for chunk in code_chunks
    )

    assert reconstructed == code.text


# ============================================================
# 7. ROUTER → TABLE CHUNKER
# ============================================================

def test_router_to_table_chunker():

    table = make_table(2)

    candidate = make_candidate(
        [
            make_paragraph(
                0,
                "The following table describes the system.",
            ),
            table,
        ]
    )

    router = ElementRouter()

    routed_chunks = router.route(candidate)

    table_route = next(
        chunk
        for chunk in routed_chunks
        if chunk.chunk_type == ChunkType.TABLE
    )

    chunker = TableChunker(
        max_tokens=1000,
    )

    table_chunks = chunker.chunk(
        table_route
    )

    assert len(table_chunks) >= 1

    assert all(
        chunk.elements == [table]
        for chunk in table_chunks
    )

    assert all(
        chunk.metadata["is_table_chunk"] is True
        for chunk in table_chunks
    )

    assert all(
        chunk.metadata["has_header_row"] is True
        for chunk in table_chunks
    )


# ============================================================
# 8. FULL MIXED ROUTER → SPECIALIZED CHUNKERS FLOW
# ============================================================

def test_full_router_to_specialized_chunkers():

    paragraph_0 = make_paragraph(
        0,
        "Intellex uses RAG for enterprise knowledge.",
    )

    paragraph_1 = make_paragraph(
        1,
        "The retriever searches the knowledge base.",
    )

    table = make_table(2)

    code = make_code(
        3,
        (
            "def retrieve(query):\n"
            "    return search(query)\n"
        ),
        language="python",
    )

    paragraph_4 = make_paragraph(
        4,
        "The generator uses retrieved context.",
    )

    elements = [
        paragraph_0,
        paragraph_1,
        table,
        code,
        paragraph_4,
    ]

    candidate = make_candidate(
        elements
    )

    router = ElementRouter()

    routed_chunks = router.route(
        candidate
    )

    # --------------------------------------------------------
    # Router verification
    # --------------------------------------------------------

    assert len(routed_chunks) == 3

    assert [
        chunk.chunk_type
        for chunk in routed_chunks
    ] == [
        ChunkType.NARRATIVE,
        ChunkType.TABLE,
        ChunkType.CODE,
    ]

    # --------------------------------------------------------
    # Process each route
    # --------------------------------------------------------

    narrative_route = next(
        chunk
        for chunk in routed_chunks
        if chunk.chunk_type == ChunkType.NARRATIVE
    )

    table_route = next(
        chunk
        for chunk in routed_chunks
        if chunk.chunk_type == ChunkType.TABLE
    )

    code_route = next(
        chunk
        for chunk in routed_chunks
        if chunk.chunk_type == ChunkType.CODE
    )

    # --------------------------------------------------------
    # Narrative
    # --------------------------------------------------------

    narrative_splitter = NarrativeSafetySplitter(
        max_tokens=1000,
    )

    narrative_chunks = narrative_splitter.split(
        narrative_route
    )

    assert len(narrative_chunks) == 1

    assert [
        element.order_index
        for element in narrative_chunks[0].elements
    ] == [0, 1, 4]

    # --------------------------------------------------------
    # Code
    # --------------------------------------------------------

    code_chunker = CodeChunker(
        max_tokens=1000,
    )

    code_chunks = code_chunker.chunk(
        code_route
    )

    assert len(code_chunks) >= 1

    assert all(
        chunk.elements == [code]
        for chunk in code_chunks
    )

    # --------------------------------------------------------
    # Table
    # --------------------------------------------------------

    table_chunker = TableChunker(
        max_tokens=1000,
    )

    table_chunks = table_chunker.chunk(
        table_route
    )

    assert len(table_chunks) >= 1

    assert all(
        chunk.elements == [table]
        for chunk in table_chunks
    )

    # --------------------------------------------------------
    # Verify source elements are preserved
    # --------------------------------------------------------

    narrative_ids = {
        element.order_index
        for chunk in narrative_chunks
        for element in chunk.elements
    }

    table_ids = {
        element.order_index
        for chunk in table_chunks
        for element in chunk.elements
    }

    code_ids = {
        element.order_index
        for chunk in code_chunks
        for element in chunk.elements
    }

    assert narrative_ids == {0, 1, 4}

    assert table_ids == {2}

    assert code_ids == {3}

    # Every source element was routed to exactly one path.
    all_ids = (
        narrative_ids
        | table_ids
        | code_ids
    )

    assert all_ids == {0, 1, 2, 3, 4}


# ============================================================
# 9. NO CROSS-TYPE CONTAMINATION
# ============================================================

def test_no_cross_type_contamination():

    table = make_table(2)

    code = make_code(
        3,
        "def hello():\n    return True",
    )

    candidate = make_candidate(
        [
            make_paragraph(
                0,
                "Narrative content.",
            ),
            table,
            code,
        ]
    )

    router = ElementRouter()

    routed_chunks = router.route(
        candidate
    )

    narrative_route = next(
        chunk
        for chunk in routed_chunks
        if chunk.chunk_type == ChunkType.NARRATIVE
    )

    table_route = next(
        chunk
        for chunk in routed_chunks
        if chunk.chunk_type == ChunkType.TABLE
    )

    code_route = next(
        chunk
        for chunk in routed_chunks
        if chunk.chunk_type == ChunkType.CODE
    )

    # Narrative must not contain table/code.
    assert all(
        element.element_type
        not in {
            ElementType.TABLE,
            ElementType.CODE_BLOCK,
        }
        for element in narrative_route.elements
    )

    # Table must contain only table.
    assert all(
        element.element_type == ElementType.TABLE
        for element in table_route.elements
    )

    # Code must contain only code.
    assert all(
        element.element_type == ElementType.CODE_BLOCK
        for element in code_route.elements
    )


# ============================================================
# 10. ORDER PRESERVATION
# ============================================================

def test_router_preserves_order_index():

    elements = [
        make_paragraph(
            5,
            "Later paragraph.",
        ),

        make_code(
            2,
            "def test():\n    pass",
        ),

        make_table(4),

        make_paragraph(
            0,
            "First paragraph.",
        ),
    ]

    candidate = make_candidate(
        elements
    )

    router = ElementRouter()

    routed_chunks = router.route(
        candidate
    )

    assert [
        chunk.order_index
        for chunk in routed_chunks
    ] == [0, 2, 4]