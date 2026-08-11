from app.dto.chunk_candidate import ChunkCandidate
from app.dto.extracted_element import ExtractedElement
from app.enums.chunk_type import ChunkType
from app.enums.element_type import ElementType
from app.services.chunking.routing.element_router import ElementRouter


def paragraph_element(order_index: int, text: str = "Paragraph") -> ExtractedElement:
    return ExtractedElement(
        order_index=order_index,
        text=text,
        element_type=ElementType.PARAGRAPH,
        metadata={},
    )


def table_element(order_index: int, text: str = "Table") -> ExtractedElement:
    return ExtractedElement(
        order_index=order_index,
        text=text,
        element_type=ElementType.TABLE,
        metadata={},
    )


def code_element(order_index: int, text: str = "print('hello')") -> ExtractedElement:
    return ExtractedElement(
        order_index=order_index,
        text=text,
        element_type=ElementType.CODE_BLOCK,
        metadata={},
    )


def make_candidate(elements, text="Section: Test", heading="Test", section_path=None):
    return ChunkCandidate(
        text=text,
        elements=elements,
        heading=heading,
        section_path=section_path or ["Test"],
    )


# ---------------------------------------------------------------------------
# 1. Narrative only
# ---------------------------------------------------------------------------

def test_routes_narrative_elements():
    paragraph = paragraph_element(1, "Intellex is an AI platform.")

    candidate = make_candidate(
        elements=[paragraph],
        text="Section: Introduction\n\nIntellex is an AI platform.",
        heading="Introduction",
        section_path=["Introduction"],
    )

    result = ElementRouter().route(candidate)

    assert len(result) == 1
    assert result[0].chunk_type == ChunkType.NARRATIVE
    assert result[0].text == candidate.text
    assert result[0].elements == [paragraph]
    assert result[0].section_path == ["Introduction"]
    assert result[0].order_index == 1


# ---------------------------------------------------------------------------
# 2. Narrative + table
# ---------------------------------------------------------------------------

def test_routes_narrative_and_table_without_rebuilding_text():
    p1 = paragraph_element(1, "First paragraph.")
    table = table_element(2)
    p2 = paragraph_element(3, "Second paragraph.")

    candidate = make_candidate(
        elements=[p1, table, p2],
        text="Section: Introduction\n\nFirst paragraph.\n\nSecond paragraph.",
        heading="Introduction",
        section_path=["Introduction"],
    )

    result = ElementRouter().route(candidate)

    assert len(result) == 2

    narrative = result[0]
    routed_table = result[1]

    assert narrative.chunk_type == ChunkType.NARRATIVE
    assert narrative.elements == [p1, p2]
    assert narrative.text == candidate.text
    assert narrative.order_index == 1

    assert routed_table.chunk_type == ChunkType.TABLE
    assert routed_table.elements == [table]
    assert routed_table.text is None
    assert routed_table.order_index == 2


# ---------------------------------------------------------------------------
# 3. Table only
# ---------------------------------------------------------------------------

def test_routes_table_only():
    table = table_element(5)

    candidate = make_candidate(
        elements=[table],
        text="Section: Pricing",
        heading="Pricing",
        section_path=["Pricing"],
    )

    result = ElementRouter().route(candidate)

    assert len(result) == 1
    assert result[0].chunk_type == ChunkType.TABLE
    assert result[0].elements == [table]
    assert result[0].text is None
    assert result[0].section_path == ["Pricing"]
    assert result[0].order_index == 5


# ---------------------------------------------------------------------------
# 4. Code only
# ---------------------------------------------------------------------------

def test_routes_code_only():
    code = code_element(7)

    candidate = make_candidate(
        elements=[code],
        text="Section: Implementation",
        heading="Implementation",
        section_path=["Implementation"],
    )

    result = ElementRouter().route(candidate)

    assert len(result) == 1
    assert result[0].chunk_type == ChunkType.CODE
    assert result[0].elements == [code]
    assert result[0].text is None
    assert result[0].section_path == ["Implementation"]
    assert result[0].order_index == 7


# ---------------------------------------------------------------------------
# 5. Mixed ordering
# ---------------------------------------------------------------------------

def test_routes_mixed_elements_in_document_order():
    p1 = paragraph_element(10, "First paragraph.")
    table = table_element(11)
    p2 = paragraph_element(12, "Second paragraph.")
    code = code_element(13)

    candidate = make_candidate(
        elements=[p1, table, p2, code],
        text=(
            "Section: Mixed\n\n"
            "First paragraph.\n\n"
            "Second paragraph."
        ),
        heading="Mixed",
        section_path=["Mixed"],
    )

    result = ElementRouter().route(candidate)

    assert len(result) == 3

    assert [chunk.chunk_type for chunk in result] == [
        ChunkType.NARRATIVE,
        ChunkType.TABLE,
        ChunkType.CODE,
    ]

    assert [chunk.order_index for chunk in result] == [10, 11, 13]

    assert result[0].elements == [p1, p2]
    assert result[0].text == candidate.text

    assert result[1].elements == [table]
    assert result[1].text is None

    assert result[2].elements == [code]
    assert result[2].text is None


# ---------------------------------------------------------------------------
# 6. Narrative order is based on the first narrative element
# ---------------------------------------------------------------------------

def test_narrative_order_index_uses_first_narrative_element():
    p1 = paragraph_element(20, "First.")
    table = table_element(21)
    p2 = paragraph_element(22, "Second.")

    candidate = make_candidate(
        elements=[p1, table, p2],
        text="Section: Test\n\nFirst.\n\nSecond.",
    )

    result = ElementRouter().route(candidate)

    assert result[0].chunk_type == ChunkType.NARRATIVE
    assert result[0].order_index == 20


# ---------------------------------------------------------------------------
# 7. Elements supplied out of order
# ---------------------------------------------------------------------------

def test_router_uses_element_order_index_not_list_position():
    p1 = paragraph_element(30, "First.")
    table = table_element(31)
    p2 = paragraph_element(32, "Second.")

    # Deliberately provide elements in a strange list order.
    candidate = make_candidate(
        elements=[p2, table, p1],
        text="Section: Test\n\nFirst.\n\nSecond.",
    )

    result = ElementRouter().route(candidate)

    assert len(result) == 2

    narrative = next(
        chunk for chunk in result
        if chunk.chunk_type == ChunkType.NARRATIVE
    )

    assert narrative.order_index == 30
    assert narrative.elements == [p2, p1]


# ---------------------------------------------------------------------------
# 8. Multiple tables
# ---------------------------------------------------------------------------

def test_multiple_tables_create_separate_table_chunks():
    table1 = table_element(40, "Table 1")
    table2 = table_element(41, "Table 2")
    table3 = table_element(42, "Table 3")

    candidate = make_candidate(
        elements=[table1, table2, table3],
        text="Section: Data",
        heading="Data",
        section_path=["Data"],
    )

    result = ElementRouter().route(candidate)

    assert len(result) == 3
    assert [chunk.chunk_type for chunk in result] == [
        ChunkType.TABLE,
        ChunkType.TABLE,
        ChunkType.TABLE,
    ]
    assert [chunk.order_index for chunk in result] == [40, 41, 42]
    assert [chunk.elements for chunk in result] == [
        [table1],
        [table2],
        [table3],
    ]
    assert all(chunk.text is None for chunk in result)


# ---------------------------------------------------------------------------
# 9. Multiple code blocks
# ---------------------------------------------------------------------------

def test_multiple_code_blocks_create_separate_code_chunks():
    code1 = code_element(50, "print('one')")
    code2 = code_element(51, "print('two')")

    candidate = make_candidate(
        elements=[code1, code2],
        text="Section: Code",
        heading="Code",
        section_path=["Code"],
    )

    result = ElementRouter().route(candidate)

    assert len(result) == 2
    assert [chunk.chunk_type for chunk in result] == [
        ChunkType.CODE,
        ChunkType.CODE,
    ]
    assert [chunk.order_index for chunk in result] == [50, 51]
    assert all(chunk.text is None for chunk in result)


# ---------------------------------------------------------------------------
# 10. Paragraphs + multiple delegated elements
# ---------------------------------------------------------------------------

def test_mixed_multiple_tables_and_code_keep_one_narrative_chunk():
    p1 = paragraph_element(60, "Intro.")
    table1 = table_element(61)
    p2 = paragraph_element(62, "Explanation.")
    code = code_element(63)
    table2 = table_element(64)
    p3 = paragraph_element(65, "Conclusion.")

    candidate = make_candidate(
        elements=[p1, table1, p2, code, table2, p3],
        text=(
            "Section: System\n\n"
            "Intro.\n\n"
            "Explanation.\n\n"
            "Conclusion."
        ),
        heading="System",
        section_path=["System"],
    )

    result = ElementRouter().route(candidate)

    assert len(result) == 4

    assert [chunk.chunk_type for chunk in result] == [
        ChunkType.NARRATIVE,
        ChunkType.TABLE,
        ChunkType.CODE,
        ChunkType.TABLE,
    ]

    assert [chunk.order_index for chunk in result] == [60, 61, 63, 64]

    assert result[0].elements == [p1, p2, p3]
    assert result[0].text == candidate.text


# ---------------------------------------------------------------------------
# 11. Whitespace-only candidate text
# ---------------------------------------------------------------------------

def test_whitespace_only_candidate_text_does_not_create_narrative_chunk():
    paragraph = paragraph_element(70, "Actual paragraph.")

    candidate = make_candidate(
        elements=[paragraph],
        text="   ",
        heading="Test",
        section_path=["Test"],
    )

    result = ElementRouter().route(candidate)

    assert result == []


# ---------------------------------------------------------------------------
# 12. Empty candidate
# ---------------------------------------------------------------------------

def test_empty_candidate_returns_no_chunks():
    candidate = make_candidate(
        elements=[],
        text="Section: Empty",
        heading="Empty",
        section_path=["Empty"],
    )

    result = ElementRouter().route(candidate)

    assert result == []


# ---------------------------------------------------------------------------
# 13. Empty text with delegated element
# ---------------------------------------------------------------------------

def test_empty_text_with_table_still_routes_table():
    table = table_element(80)

    candidate = make_candidate(
        elements=[table],
        text="",
        heading="Data",
        section_path=["Data"],
    )

    result = ElementRouter().route(candidate)

    assert len(result) == 1
    assert result[0].chunk_type == ChunkType.TABLE
    assert result[0].elements == [table]
    assert result[0].text is None


# ---------------------------------------------------------------------------
# 14. Section path is preserved
# ---------------------------------------------------------------------------

def test_section_path_is_preserved_for_all_routed_chunks():
    p1 = paragraph_element(90)
    table = table_element(91)
    code = code_element(92)

    path = ["Intellex", "RAG", "Hybrid Retrieval"]

    candidate = make_candidate(
        elements=[p1, table, code],
        text="Section: Intellex > RAG > Hybrid Retrieval\n\nParagraph",
        heading="Hybrid Retrieval",
        section_path=path,
    )

    result = ElementRouter().route(candidate)

    assert len(result) == 3

    assert all(chunk.section_path == path for chunk in result)


# ---------------------------------------------------------------------------
# 15. Narrative element order can have gaps
# ---------------------------------------------------------------------------

def test_narrative_order_index_handles_gaps():
    p1 = paragraph_element(100, "First.")
    p2 = paragraph_element(105, "Second.")

    candidate = make_candidate(
        elements=[p1, p2],
        text="Section: Test\n\nFirst.\n\nSecond.",
    )

    result = ElementRouter().route(candidate)

    assert len(result) == 1
    assert result[0].chunk_type == ChunkType.NARRATIVE
    assert result[0].order_index == 100
    assert result[0].elements == [p1, p2]


# ---------------------------------------------------------------------------
# 16. Narrative + table + code with non-contiguous positions
# ---------------------------------------------------------------------------

def test_mixed_non_contiguous_order_indices():
    p1 = paragraph_element(200, "First.")
    table = table_element(250)
    p2 = paragraph_element(300, "Second.")
    code = code_element(450)

    candidate = make_candidate(
        elements=[p1, table, p2, code],
        text="Section: Test\n\nFirst.\n\nSecond.",
    )

    result = ElementRouter().route(candidate)

    assert [chunk.order_index for chunk in result] == [200, 250, 450]


# ---------------------------------------------------------------------------
# 17. Table and code retain their exact element objects
# ---------------------------------------------------------------------------

def test_delegated_chunks_preserve_original_element_objects():
    table = table_element(300)
    code = code_element(301)

    candidate = make_candidate(
        elements=[table, code],
        text="Section: Test",
    )

    result = ElementRouter().route(candidate)

    assert result[0].elements[0] is table
    assert result[1].elements[0] is code


# ---------------------------------------------------------------------------
# 18. Narrative chunk preserves the original candidate text exactly
# ---------------------------------------------------------------------------

def test_narrative_text_is_not_reconstructed():
    paragraph = paragraph_element(400, "Paragraph.")

    original_text = (
        "Section: Intellex > RAG\n\n"
        "Paragraph."
    )

    candidate = make_candidate(
        elements=[paragraph],
        text=original_text,
        heading="RAG",
        section_path=["Intellex", "RAG"],
    )

    result = ElementRouter().route(candidate)

    assert result[0].text == original_text
    assert result[0].text is candidate.text