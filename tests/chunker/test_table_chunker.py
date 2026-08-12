from app.services.chunking.table.table_chunker import TableChunker
from app.dto.extracted_element import ExtractedElement
from app.dto.routed_chunk import RoutedChunk
from app.enums.element_type import ElementType


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def make_table_element(
    cells,
    has_header_row=True,
    table_id="table-1",
):
    """
    Create a fake TABLE ExtractedElement with the
    metadata expected by TableChunker.
    """

    text = "\n".join(
        " | ".join(row)
        for row in cells
    )

    return ExtractedElement(
        order_index=1,
        text=text,
        element_type=ElementType.TABLE,
        metadata={
            "table_id": table_id,
            "cells": cells,
            "n_rows": len(cells),
            "n_cols": max(
                (len(row) for row in cells),
                default=0,
            ),
            "has_header_row": has_header_row,
            "source": "test",
        },
    )


def make_routed_chunk(
    table_element,
    section_path=None,
):
    """
    Create a RoutedChunk containing one table.
    """

    return RoutedChunk(
        text=table_element.text,
        elements=[table_element],
        chunk_type="TABLE",
        order_index=table_element.order_index,
        section_path=section_path or ["Test Section"],
    )


# =========================================================
# 1. NORMAL TABLE
# =========================================================

def test_normal_table_creates_one_chunk():

    cells = [
        ["Name", "Age", "Department"],
        ["Alice", "20", "Engineering"],
        ["Bob", "21", "HR"],
        ["Charlie", "22", "Finance"],
    ]

    table = make_table_element(cells)

    routed_chunk = make_routed_chunk(table)

    chunker = TableChunker(max_tokens=1000)

    chunks = chunker.chunk(routed_chunk)

    assert len(chunks) == 1

    assert chunks[0].metadata["cells"] == cells

    assert chunks[0].metadata["table_id"] == "table-1"

    assert chunks[0].metadata["table_chunk_index"] == 0

    assert chunks[0].metadata["table_chunk_count"] == 1


# =========================================================
# 2. LARGE TABLE SHOULD SPLIT
# =========================================================

def test_large_table_creates_multiple_chunks():

    cells = [
        ["ID", "Name", "Description"],
        ["1", "Alice", "A" * 100],
        ["2", "Bob", "B" * 100],
        ["3", "Charlie", "C" * 100],
        ["4", "Diana", "D" * 100],
        ["5", "Ethan", "E" * 100],
        ["6", "Frank", "F" * 100],
        ["7", "Grace", "G" * 100],
        ["8", "Henry", "H" * 100],
    ]

    table = make_table_element(cells)

    routed_chunk = make_routed_chunk(table)

    # Very small limit forces recursive splitting.
    chunker = TableChunker(max_tokens=20)

    chunks = chunker.chunk(routed_chunk)

    assert len(chunks) > 1


# =========================================================
# 3. EVERY CHUNK MUST KEEP THE HEADER
# =========================================================

def test_every_chunk_preserves_header():

    header = ["ID", "Name", "Description"]

    cells = [
        header,
        ["1", "Alice", "A" * 100],
        ["2", "Bob", "B" * 100],
        ["3", "Charlie", "C" * 100],
        ["4", "Diana", "D" * 100],
        ["5", "Ethan", "E" * 100],
        ["6", "Frank", "F" * 100],
        ["7", "Grace", "G" * 100],
        ["8", "Henry", "H" * 100],
    ]

    table = make_table_element(cells)

    routed_chunk = make_routed_chunk(table)

    chunker = TableChunker(max_tokens=20)

    chunks = chunker.chunk(routed_chunk)

    assert len(chunks) > 1

    for chunk in chunks:
        assert chunk.metadata["cells"][0] == header


# =========================================================
# 4. ALL CHUNKS MUST HAVE SAME TABLE ID
# =========================================================

def test_all_chunks_keep_same_table_id():

    cells = [
        ["ID", "Name"],
        ["1", "Alice" * 20],
        ["2", "Bob" * 20],
        ["3", "Charlie" * 20],
        ["4", "Diana" * 20],
    ]

    table = make_table_element(
        cells,
        table_id="important-table-123",
    )

    routed_chunk = make_routed_chunk(table)

    chunker = TableChunker(max_tokens=20)

    chunks = chunker.chunk(routed_chunk)

    assert len(chunks) > 1

    table_ids = {
        chunk.metadata["table_id"]
        for chunk in chunks
    }

    assert len(table_ids) == 1

    assert table_ids == {"important-table-123"}


# =========================================================
# 5. CHUNK INDEXING
# =========================================================

def test_chunk_indices_are_sequential():

    cells = [
        ["ID", "Name"],
        ["1", "Alice" * 20],
        ["2", "Bob" * 20],
        ["3", "Charlie" * 20],
        ["4", "Diana" * 20],
        ["5", "Ethan" * 20],
        ["6", "Frank" * 20],
    ]

    table = make_table_element(cells)

    routed_chunk = make_routed_chunk(table)

    chunker = TableChunker(max_tokens=20)

    chunks = chunker.chunk(routed_chunk)

    assert len(chunks) > 1

    assert [
        chunk.metadata["table_chunk_index"]
        for chunk in chunks
    ] == list(range(len(chunks)))


def test_every_chunk_has_correct_chunk_count():

    cells = [
        ["ID", "Name"],
        ["1", "Alice" * 20],
        ["2", "Bob" * 20],
        ["3", "Charlie" * 20],
        ["4", "Diana" * 20],
    ]

    table = make_table_element(cells)

    routed_chunk = make_routed_chunk(table)

    chunker = TableChunker(max_tokens=20)

    chunks = chunker.chunk(routed_chunk)

    assert len(chunks) > 1

    for chunk in chunks:

        assert (
            chunk.metadata["table_chunk_count"]
            == len(chunks)
        )

def test_no_header_table_preserves_all_rows_without_header():

    cells = [
        ["A" * 30, "B" * 30, "C" * 30],
        ["D" * 30, "E" * 30, "F" * 30],
        ["G" * 30, "H" * 30, "I" * 30],
        ["J" * 30, "K" * 30, "L" * 30],
    ]

    table = make_table_element(
        cells,
        has_header_row=False,
    )

    routed_chunk = make_routed_chunk(table)

    chunker = TableChunker(max_tokens=20)

    chunks = chunker.chunk(routed_chunk)

    assert len(chunks) > 1

    reconstructed_rows = []

    for chunk in chunks:
        reconstructed_rows.extend(
            chunk.metadata["cells"]
        )

    assert reconstructed_rows == cells

# =========================================================
# 8. EMPTY TABLE
# =========================================================

def test_empty_table_returns_no_chunks():

    table = make_table_element(
        cells=[],
        has_header_row=False,
    )

    routed_chunk = make_routed_chunk(table)

    chunker = TableChunker()

    chunks = chunker.chunk(routed_chunk)

    assert chunks == []


# =========================================================
# 9. EMPTY ROUTED CHUNK
# =========================================================

def test_empty_routed_chunk_returns_no_chunks():

    routed_chunk = RoutedChunk(
        text=None,
        elements=[],
        chunk_type="TABLE",
        order_index=1,
        section_path=["Test"],
    )

    chunker = TableChunker()

    chunks = chunker.chunk(routed_chunk)

    assert chunks == []


# =========================================================
# 10. MARKDOWN METADATA MUST MATCH CHUNK TEXT
# =========================================================

def test_chunk_markdown_metadata_matches_chunk_text():

    cells = [
        ["ID", "Name", "Description"],
        ["1", "Alice", "A" * 100],
        ["2", "Bob", "B" * 100],
        ["3", "Charlie", "C" * 100],
        ["4", "Diana", "D" * 100],
        ["5", "Ethan", "E" * 100],
    ]

    table = make_table_element(cells)

    routed_chunk = make_routed_chunk(table)

    chunker = TableChunker(max_tokens=20)

    chunks = chunker.chunk(routed_chunk)

    assert len(chunks) > 1

    for chunk in chunks:

        assert chunk.metadata["markdown"] == chunk.text


# =========================================================
# 11. MARKDOWN SHOULD ONLY CONTAIN THAT CHUNK'S ROWS
# =========================================================

def test_chunk_markdown_contains_only_its_own_rows():

    cells = [
        ["ID", "Name"],
        ["1", "Alice" * 30],
        ["2", "Bob" * 30],
        ["3", "Charlie" * 30],
        ["4", "Diana" * 30],
    ]

    table = make_table_element(cells)

    routed_chunk = make_routed_chunk(table)

    chunker = TableChunker(max_tokens=20)

    chunks = chunker.chunk(routed_chunk)

    assert len(chunks) > 1

    for chunk in chunks:

        chunk_cells = chunk.metadata["cells"]

        markdown = chunk.metadata["markdown"]

        # Header must be present.
        assert "ID" in markdown
        assert "Name" in markdown

        # Every row belonging to this chunk should appear
        # in its markdown representation.
        for row in chunk_cells:

            row_text = " | ".join(row)

            assert row_text in markdown


# =========================================================
# 12. SECTION PATH IS PRESERVED
# =========================================================

def test_section_path_is_preserved():

    cells = [
        ["ID", "Name"],
        ["1", "Alice"],
        ["2", "Bob"],
    ]

    table = make_table_element(cells)

    routed_chunk = make_routed_chunk(
        table,
        section_path=[
            "Intellex",
            "RAG",
            "Tables",
        ],
    )

    chunker = TableChunker()

    chunks = chunker.chunk(routed_chunk)

    assert len(chunks) == 1

    assert chunks[0].metadata["section_path"] == [
        "Intellex",
        "RAG",
        "Tables",
    ]


# =========================================================
# 13. TABLE ELEMENT ITSELF IS PRESERVED
# =========================================================

def test_original_table_element_is_preserved():

    cells = [
        ["ID", "Name"],
        ["1", "Alice"],
        ["2", "Bob"],
    ]

    table = make_table_element(cells)

    routed_chunk = make_routed_chunk(table)

    chunker = TableChunker()

    chunks = chunker.chunk(routed_chunk)

    assert len(chunks) == 1

    assert chunks[0].elements[0] is table


# =========================================================
# 14. IS_TABLE_CHUNK METADATA
# =========================================================

def test_is_table_chunk_metadata_is_true():

    cells = [
        ["ID", "Name"],
        ["1", "Alice"],
        ["2", "Bob"],
    ]

    table = make_table_element(cells)

    routed_chunk = make_routed_chunk(table)

    chunker = TableChunker()

    chunks = chunker.chunk(routed_chunk)

    assert len(chunks) == 1

    assert chunks[0].metadata["is_table_chunk"] is True


# =========================================================
# 15. N_ROWS AND N_COLS MATCH CHUNK CELLS
# =========================================================

def test_chunk_dimensions_match_chunk_cells():

    cells = [
        ["ID", "Name", "Age"],
        ["1", "Alice", "20"],
        ["2", "Bob", "21"],
        ["3", "Charlie", "22"],
    ]

    table = make_table_element(cells)

    routed_chunk = make_routed_chunk(table)

    chunker = TableChunker()

    chunks = chunker.chunk(routed_chunk)

    assert len(chunks) == 1

    chunk = chunks[0]

    assert chunk.metadata["n_rows"] == len(
        chunk.metadata["cells"]
    )

    assert chunk.metadata["n_cols"] == max(
        len(row)
        for row in chunk.metadata["cells"]
    )