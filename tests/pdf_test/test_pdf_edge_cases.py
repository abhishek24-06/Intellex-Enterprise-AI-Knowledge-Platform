import os
from pathlib import Path

import pytest

os.environ["TORCH_COMPILE_DISABLE"] = "1"

from app.services.extraction.pdf.pdf_extractor import PdfExtractor
from app.enums.element_type import ElementType


# ============================================================
# OPTIONAL TEST DEPENDENCY
# ============================================================

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas

    REPORTLAB_AVAILABLE = True

except ImportError:
    REPORTLAB_AVAILABLE = False


# ============================================================
# HELPERS
# ============================================================

def require_reportlab():
    """
    Skip generated-PDF tests if reportlab is not installed.
    """
    if not REPORTLAB_AVAILABLE:
        pytest.skip(
            "reportlab is required for generated PDF edge-case tests"
        )


def create_pdf(
    path: Path,
    pages: list[list[str]],
):
    """
    Create a simple multi-page PDF.

    Each inner list represents one page.
    """
    require_reportlab()

    pdf = canvas.Canvas(
        str(path),
        pagesize=A4,
    )

    width, height = A4

    for page_lines in pages:

        y = height - 60

        for line in page_lines:

            pdf.drawString(
                50,
                y,
                str(line),
            )

            y -= 18

            if y < 50:
                break

        pdf.showPage()

    pdf.save()

    assert path.exists()
    assert path.stat().st_size > 0


def create_table_pdf(
    path: Path,
    rows: list[list[str]],
):
    """
    Create a PDF containing a visually structured table.

    This is primarily useful for testing that the extractor
    does not crash and returns valid table metadata when
    Docling recognizes the table.
    """
    require_reportlab()

    from reportlab.platypus import (
        SimpleDocTemplate,
        Table,
        TableStyle,
        Paragraph,
    )

    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet

    styles = getSampleStyleSheet()

    document = SimpleDocTemplate(
        str(path),
        pagesize=A4,
    )

    data = []

    for row in rows:

        data.append(
            [
                Paragraph(
                    str(cell),
                    styles["BodyText"],
                )
                for cell in row
            ]
        )

    table = Table(data)

    table.setStyle(
        TableStyle(
            [
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    1,
                    colors.black,
                ),
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, 0),
                    colors.lightgrey,
                ),
                (
                    "VALIGN",
                    (0, 0),
                    (-1, -1),
                    "MIDDLE",
                ),
            ]
        )
    )

    document.build([table])

    assert path.exists()
    assert path.stat().st_size > 0


def extract_pdf(
    pdf_path: Path,
    document_id: str = "edge-test",
    filename: str | None = None,
):
    """
    Convenience wrapper around PdfExtractor.
    """
    extractor = PdfExtractor()

    return extractor.extract(
        pdf_path,
        document_id=document_id,
        filename=filename or pdf_path.name,
    )


def elements_of_type(
    result,
    element_type,
):
    """
    Return all elements of a specific ElementType.
    """
    return [
        element
        for element in result.elements
        if element.element_type == element_type
    ]


def assert_valid_result(result):
    """
    Common result validation.
    """
    assert result is not None
    assert result.elements is not None


def assert_valid_ordering(result):
    """
    Verify order_index integrity.
    """
    elements = result.elements

    order_indices = [
        element.order_index
        for element in elements
    ]

    assert len(order_indices) == len(
        set(order_indices)
    ), "Duplicate order_index detected"

    assert order_indices == sorted(
        order_indices
    ), "Elements are not sorted by order_index"

    for element in elements:
        assert element.order_index is not None


def assert_common_metadata(
    result,
    document_id,
    filename,
):
    """
    Verify metadata shared by all extracted elements.
    """
    for element in result.elements:

        metadata = element.metadata

        assert metadata is not None

        assert metadata.get("document_id") == document_id

        assert metadata.get("filename") == filename

        assert metadata.get("source") == "docling"


# ============================================================
# REAL PDF TEST
# ============================================================

def test_extract_real_pdf():

    # ========================================================
    # INPUT / OUTPUT PATHS
    # ========================================================

    test_dir = Path(__file__).parent

    # Real PDF
    pdf_path = test_dir / "report.pdf"

    # Extracted output
    output_path = test_dir / "extracted_code.txt"

    # Make sure PDF exists
    assert pdf_path.exists(), (
        f"PDF not found: {pdf_path}"
    )

    # ========================================================
    # RUN PDF EXTRACTOR
    # ========================================================

    extractor = PdfExtractor()

    result = extractor.extract(
        pdf_path,
        document_id="real-pdf-test",
        filename=pdf_path.name,
    )

    # ========================================================
    # BASIC VALIDATION
    # ========================================================

    assert result is not None
    assert result.elements is not None

    elements = result.elements

    assert len(elements) > 0, (
        "PDF extraction returned no elements"
    )

    # ========================================================
    # COUNT ELEMENT TYPES
    # ========================================================

    heading_count = 0
    paragraph_count = 0
    list_count = 0
    table_count = 0
    code_count = 0
    image_count = 0

    for element in elements:

        if element.element_type == ElementType.HEADING:
            heading_count += 1

        elif element.element_type == ElementType.PARAGRAPH:
            paragraph_count += 1

        elif element.element_type == ElementType.LIST:
            list_count += 1

        elif element.element_type == ElementType.TABLE:
            table_count += 1

        elif element.element_type == ElementType.CODE_BLOCK:
            code_count += 1

        elif element.element_type == ElementType.IMAGE:
            image_count += 1

    # ========================================================
    # WRITE EVERYTHING TO TXT
    # ========================================================

    with output_path.open(
        "w",
        encoding="utf-8",
    ) as f:

        f.write("=" * 100 + "\n")
        f.write("REAL PDF EXTRACTION TEST RESULT\n")
        f.write("=" * 100 + "\n\n")

        f.write(
            f"Input PDF     : {pdf_path}\n"
        )

        f.write(
            f"Output TXT    : {output_path}\n"
        )

        f.write(
            f"Total elements: {len(elements)}\n\n"
        )

        # ----------------------------------------------------
        # ELEMENT COUNTS
        # ----------------------------------------------------

        f.write("=" * 100 + "\n")
        f.write("ELEMENT COUNTS\n")
        f.write("=" * 100 + "\n\n")

        f.write(
            f"Headings   : {heading_count}\n"
        )

        f.write(
            f"Paragraphs : {paragraph_count}\n"
        )

        f.write(
            f"Lists      : {list_count}\n"
        )

        f.write(
            f"Tables     : {table_count}\n"
        )

        f.write(
            f"Code       : {code_count}\n"
        )

        f.write(
            f"Images     : {image_count}\n\n"
        )

        # ----------------------------------------------------
        # ALL ELEMENTS
        # ----------------------------------------------------

        f.write("=" * 100 + "\n")
        f.write("EXTRACTED ELEMENTS\n")
        f.write("=" * 100 + "\n\n")

        for element in elements:

            f.write("-" * 100 + "\n")

            f.write(
                f"Order Index : {element.order_index}\n"
            )

            f.write(
                f"Element Type: {element.element_type}\n"
            )

            f.write(
                f"Metadata    : {element.metadata}\n\n"
            )

            # ------------------------------------------------
            # TABLE INFORMATION
            # ------------------------------------------------

            if element.element_type == ElementType.TABLE:

                metadata = element.metadata

                f.write("TABLE INFORMATION\n")
                f.write("-" * 50 + "\n")

                f.write(
                    f"Table Index : "
                    f"{metadata.get('table_index')}\n"
                )

                f.write(
                    f"Table ID    : "
                    f"{metadata.get('table_id')}\n"
                )

                f.write(
                    f"Rows        : "
                    f"{metadata.get('n_rows')}\n"
                )

                f.write(
                    f"Columns     : "
                    f"{metadata.get('n_cols')}\n"
                )

                f.write(
                    f"Header Row  : "
                    f"{metadata.get('has_header_row')}\n"
                )

                f.write("\n")

            # ------------------------------------------------
            # TEXT
            # ------------------------------------------------

            f.write("TEXT:\n")

            text = getattr(
                element,
                "text",
                None,
            )

            if text:
                f.write(str(text))
            else:
                f.write("[NO TEXT]")

            f.write("\n\n")

            # ------------------------------------------------
            # TABLE MARKDOWN
            # ------------------------------------------------

            if element.element_type == ElementType.TABLE:

                markdown = element.metadata.get(
                    "markdown"
                )

                if markdown:

                    f.write(
                        "TABLE MARKDOWN:\n"
                    )

                    f.write(
                        "-" * 50 + "\n"
                    )

                    f.write(
                        str(markdown)
                    )

                    f.write("\n\n")

    # ========================================================
    # VALIDATION
    # ========================================================

    assert_valid_ordering(result)

    assert_common_metadata(
        result,
        "real-pdf-test",
        pdf_path.name,
    )

    # --------------------------------------------------------
    # TABLE VALIDATION
    # --------------------------------------------------------

    tables = elements_of_type(
        result,
        ElementType.TABLE,
    )

    if tables:

        table_indices = [
            table.metadata.get(
                "table_index"
            )
            for table in tables
        ]

        assert all(
            index is not None
            for index in table_indices
        )

        assert len(table_indices) == len(
            set(table_indices)
        )

        expected_table_indices = list(
            range(len(tables))
        )

        assert sorted(
            table_indices
        ) == expected_table_indices

        table_ids = [
            table.metadata.get(
                "table_id"
            )
            for table in tables
        ]

        assert all(
            table_id is not None
            for table_id in table_ids
        )

        assert len(table_ids) == len(
            set(table_ids)
        )

        # ----------------------------------------------------
        # TABLE DIMENSIONS
        # ----------------------------------------------------

        for table in tables:

            metadata = table.metadata

            n_rows = metadata.get(
                "n_rows"
            )

            n_cols = metadata.get(
                "n_cols"
            )

            cells = metadata.get(
                "cells"
            )

            assert n_rows is not None

            assert n_cols is not None

            assert n_rows > 0

            assert n_cols > 0

            assert cells is not None

            assert len(cells) == n_rows

            for row in cells:

                assert len(row) == n_cols

    # --------------------------------------------------------
    # CODE VALIDATION
    # --------------------------------------------------------

    codes = elements_of_type(
        result,
        ElementType.CODE_BLOCK,
    )

    assert len(codes) > 0, (
        "PDF contains no extracted CODE_BLOCK elements"
    )

    for code in codes:

        assert code.text is not None

        assert code.text.strip() != ""

        assert code.metadata.get(
            "page"
        ) is not None

        assert code.metadata.get(
            "source"
        ) == "docling"

    # ========================================================
    # SUCCESS
    # ========================================================

    print()
    print("=" * 70)
    print("PDF EXTRACTION TEST PASSED")
    print("=" * 70)
    print(f"PDF       : {pdf_path}")
    print(f"TXT       : {output_path}")
    print(f"Elements  : {len(elements)}")
    print(f"Tables    : {table_count}")
    print(f"Images    : {image_count}")
    print("=" * 70)


# ============================================================
# EDGE CASE 1 — EMPTY PDF
# ============================================================

def test_empty_pdf(tmp_path):

    require_reportlab()

    pdf_path = tmp_path / "empty.pdf"

    create_pdf(
        pdf_path,
        [[]],
    )

    result = extract_pdf(
        pdf_path,
        document_id="empty-pdf",
    )

    assert_valid_result(result)

    # Empty PDFs may legitimately produce zero elements.
    assert isinstance(
        result.elements,
        list,
    )


# ============================================================
# EDGE CASE 2 — SINGLE PARAGRAPH
# ============================================================

def test_single_paragraph_pdf(tmp_path):

    pdf_path = tmp_path / "paragraph.pdf"

    create_pdf(
        pdf_path,
        [
            [
                "This is a simple PDF paragraph.",
            ]
        ],
    )

    result = extract_pdf(
        pdf_path,
        document_id="paragraph-test",
    )

    assert_valid_result(result)

    assert len(result.elements) > 0

    assert_valid_ordering(result)


# ============================================================
# EDGE CASE 3 — MULTIPLE PARAGRAPHS
# ============================================================

def test_multiple_paragraphs_pdf(tmp_path):

    pdf_path = tmp_path / "paragraphs.pdf"

    create_pdf(
        pdf_path,
        [
            [
                "First paragraph.",
                "",
                "Second paragraph.",
                "",
                "Third paragraph.",
            ]
        ],
    )

    result = extract_pdf(
        pdf_path,
        document_id="paragraphs-test",
    )

    assert_valid_result(result)

    assert len(result.elements) > 0

    assert_valid_ordering(result)


# ============================================================
# EDGE CASE 4 — MULTI-PAGE PDF
# ============================================================

def test_multi_page_pdf(tmp_path):

    pdf_path = tmp_path / "multi_page.pdf"

    create_pdf(
        pdf_path,
        [
            [
                "Page 1",
                "Content from first page.",
            ],
            [
                "Page 2",
                "Content from second page.",
            ],
            [
                "Page 3",
                "Content from third page.",
            ],
        ],
    )

    result = extract_pdf(
        pdf_path,
        document_id="multi-page",
    )

    assert_valid_result(result)

    assert len(result.elements) > 0

    assert_valid_ordering(result)

    # At least one element should have page metadata.
    pages = [
        element.metadata.get("page")
        for element in result.elements
        if element.metadata
    ]

    assert any(
        page is not None
        for page in pages
    )


# ============================================================
# EDGE CASE 5 — UNICODE
# ============================================================

def test_unicode_pdf(tmp_path):

    pdf_path = tmp_path / "unicode.pdf"

    # ReportLab default Helvetica does not support
    # arbitrary Unicode reliably. Use characters that
    # are commonly supported by the PDF generation setup.
    create_pdf(
        pdf_path,
        [
            [
                "Unicode test: café",
                "Currency: Rs 120",
                "Symbols: + - = %",
            ]
        ],
    )

    result = extract_pdf(
        pdf_path,
        document_id="unicode-test",
    )

    assert_valid_result(result)

    assert len(result.elements) > 0


# ============================================================
# EDGE CASE 6 — VERY LONG LINE
# ============================================================

def test_very_long_line(tmp_path):

    pdf_path = tmp_path / "long_line.pdf"

    long_text = "A" * 2000

    create_pdf(
        pdf_path,
        [
            [
                long_text,
            ]
        ],
    )

    result = extract_pdf(
        pdf_path,
        document_id="long-line",
    )

    assert_valid_result(result)

    assert len(result.elements) > 0

    assert_valid_ordering(result)


# ============================================================
# EDGE CASE 7 — SPECIAL CHARACTERS
# ============================================================

def test_special_characters_pdf(tmp_path):

    pdf_path = tmp_path / "special.pdf"

    create_pdf(
        pdf_path,
        [
            [
                "Special characters: ! @ # $ % ^ & * ( )",
                "Brackets: [ ] { } < >",
                "Operators: + - * / =",
            ]
        ],
    )

    result = extract_pdf(
        pdf_path,
        document_id="special-test",
    )

    assert_valid_result(result)

    assert len(result.elements) > 0


# ============================================================
# EDGE CASE 8 — TABLE WITH HEADER
# ============================================================

def test_table_with_header(tmp_path):

    pdf_path = tmp_path / "table_header.pdf"

    create_table_pdf(
        pdf_path,
        [
            [
                "Name",
                "Age",
                "Role",
            ],
            [
                "Alice",
                "24",
                "Engineer",
            ],
            [
                "Bob",
                "28",
                "Scientist",
            ],
        ],
    )

    result = extract_pdf(
        pdf_path,
        document_id="header-table",
    )

    assert_valid_result(result)

    tables = elements_of_type(
        result,
        ElementType.TABLE,
    )

    # Docling is responsible for deciding whether the
    # visual structure is a table.
    if tables:

        table = tables[0]

        assert table.metadata.get(
            "n_rows"
        ) > 0

        assert table.metadata.get(
            "n_cols"
        ) > 0

        assert table.metadata.get(
            "cells"
        ) is not None


# ============================================================
# EDGE CASE 9 — TABLE WITH NO HEADER
# ============================================================

def test_table_without_header(tmp_path):

    pdf_path = tmp_path / "table_no_header.pdf"

    create_table_pdf(
        pdf_path,
        [
            [
                "Alice",
                "24",
                "Engineer",
            ],
            [
                "Bob",
                "28",
                "Scientist",
            ],
            [
                "Charlie",
                "22",
                "Designer",
            ],
        ],
    )

    result = extract_pdf(
        pdf_path,
        document_id="no-header-table",
    )

    assert_valid_result(result)

    tables = elements_of_type(
        result,
        ElementType.TABLE,
    )

    if tables:

        table = tables[0]

        assert table.metadata.get(
            "n_rows"
        ) > 0

        assert table.metadata.get(
            "n_cols"
        ) > 0


# ============================================================
# EDGE CASE 10 — MULTIPLE TABLES
# ============================================================

def test_multiple_tables(tmp_path):

    require_reportlab()

    from reportlab.platypus import (
        SimpleDocTemplate,
        Table,
        TableStyle,
        Spacer,
    )

    from reportlab.lib import colors

    pdf_path = tmp_path / "multiple_tables.pdf"

    document = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
    )

    table1 = Table(
        [
            ["Name", "Age"],
            ["Alice", "24"],
            ["Bob", "28"],
        ]
    )

    table2 = Table(
        [
            ["Product", "Price"],
            ["Laptop", "75000"],
            ["Mouse", "1200"],
        ]
    )

    style = TableStyle(
        [
            (
                "GRID",
                (0, 0),
                (-1, -1),
                1,
                colors.black,
            )
        ]
    )

    table1.setStyle(style)
    table2.setStyle(style)

    document.build(
        [
            table1,
            Spacer(1, 30),
            table2,
        ]
    )

    result = extract_pdf(
        pdf_path,
        document_id="multiple-tables",
    )

    assert_valid_result(result)

    tables = elements_of_type(
        result,
        ElementType.TABLE,
    )

    if len(tables) >= 2:

        table_indices = [
            table.metadata.get(
                "table_index"
            )
            for table in tables
        ]

        assert len(
            table_indices
        ) == len(
            set(table_indices)
        )

        assert sorted(
            table_indices
        ) == list(
            range(len(tables))
        )


# ============================================================
# EDGE CASE 11 — TABLE WITH EMPTY CELLS
# ============================================================

def test_table_empty_cells(tmp_path):

    pdf_path = tmp_path / "empty_cells.pdf"

    create_table_pdf(
        pdf_path,
        [
            [
                "Name",
                "Email",
                "Phone",
            ],
            [
                "Alice",
                "",
                "12345",
            ],
            [
                "",
                "bob@example.com",
                "",
            ],
            [
                "Charlie",
                "charlie@example.com",
                "98765",
            ],
        ],
    )

    result = extract_pdf(
        pdf_path,
        document_id="empty-cells",
    )

    assert_valid_result(result)

    tables = elements_of_type(
        result,
        ElementType.TABLE,
    )

    if tables:

        table = tables[0]

        cells = table.metadata.get(
            "cells"
        )

        assert cells is not None

        assert len(cells) > 0

        for row in cells:

            assert isinstance(
                row,
                list,
            )


# ============================================================
# EDGE CASE 12 — WIDE TABLE
# ============================================================

def test_wide_table(tmp_path):

    pdf_path = tmp_path / "wide_table.pdf"

    create_table_pdf(
        pdf_path,
        [
            [
                "A",
                "B",
                "C",
                "D",
                "E",
                "F",
                "G",
                "H",
            ],
            [
                "1",
                "2",
                "3",
                "4",
                "5",
                "6",
                "7",
                "8",
            ],
        ],
    )

    result = extract_pdf(
        pdf_path,
        document_id="wide-table",
    )

    assert_valid_result(result)

    tables = elements_of_type(
        result,
        ElementType.TABLE,
    )

    if tables:

        table = tables[0]

        assert table.metadata.get(
            "n_cols"
        ) > 0


# ============================================================
# EDGE CASE 13 — LONG TABLE
# ============================================================

def test_long_table(tmp_path):

    rows = [
        [
            "ID",
            "Name",
            "Department",
            "Score",
        ]
    ]

    for i in range(1, 51):

        rows.append(
            [
                str(i),
                f"Student {i}",
                "Engineering",
                str(50 + i),
            ]
        )

    pdf_path = tmp_path / "long_table.pdf"

    create_table_pdf(
        pdf_path,
        rows,
    )

    result = extract_pdf(
        pdf_path,
        document_id="long-table",
    )

    assert_valid_result(result)

    tables = elements_of_type(
        result,
        ElementType.TABLE,
    )

    if tables:

        table = tables[0]

        assert table.metadata.get(
            "n_rows"
        ) > 0


# ============================================================
# EDGE CASE 14 — TABLE ID UNIQUENESS
# ============================================================

def test_table_ids_unique(tmp_path):

    require_reportlab()

    from reportlab.platypus import (
        SimpleDocTemplate,
        Table,
        TableStyle,
        Spacer,
    )

    from reportlab.lib import colors

    pdf_path = tmp_path / "table_ids.pdf"

    document = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
    )

    style = TableStyle(
        [
            (
                "GRID",
                (0, 0),
                (-1, -1),
                1,
                colors.black,
            )
        ]
    )

    tables_to_add = []

    for i in range(3):

        table = Table(
            [
                ["Column A", "Column B"],
                [str(i), str(i + 1)],
            ]
        )

        table.setStyle(style)

        tables_to_add.append(table)

        if i < 2:
            tables_to_add.append(
                Spacer(1, 20)
            )

    document.build(
        tables_to_add
    )

    result = extract_pdf(
        pdf_path,
        document_id="table-id-test",
    )

    assert_valid_result(result)

    tables = elements_of_type(
        result,
        ElementType.TABLE,
    )

    if tables:

        table_ids = [
            table.metadata.get(
                "table_id"
            )
            for table in tables
        ]

        table_ids = [
            table_id
            for table_id in table_ids
            if table_id is not None
        ]

        assert len(table_ids) == len(
            set(table_ids)
        )


# ============================================================
# EDGE CASE 15 — TABLE DIMENSIONS
# ============================================================

def test_table_dimensions_match_cells(tmp_path):

    pdf_path = tmp_path / "dimensions.pdf"

    create_table_pdf(
        pdf_path,
        [
            ["A", "B", "C"],
            ["1", "2", "3"],
            ["4", "5", "6"],
        ],
    )

    result = extract_pdf(
        pdf_path,
        document_id="dimension-test",
    )

    assert_valid_result(result)

    tables = elements_of_type(
        result,
        ElementType.TABLE,
    )

    for table in tables:

        metadata = table.metadata

        rows = metadata.get(
            "n_rows"
        )

        cols = metadata.get(
            "n_cols"
        )

        cells = metadata.get(
            "cells"
        )

        assert rows is not None
        assert cols is not None
        assert cells is not None

        assert rows == len(cells)

        for row in cells:

            assert len(row) == cols


# ============================================================
# EDGE CASE 16 — CODE BLOCK / MONOSPACE CONTENT
# ============================================================

def test_code_like_content_pdf(tmp_path):

    pdf_path = tmp_path / "code.pdf"

    create_pdf(
        pdf_path,
        [
            [
                "def hello():",
                "    print('Hello World')",
                "",
                "if __name__ == '__main__':",
                "    hello()",
            ]
        ],
    )

    result = extract_pdf(
        pdf_path,
        document_id="code-test",
    )

    assert_valid_result(result)

    assert len(result.elements) > 0

    assert_valid_ordering(result)


# ============================================================
# EDGE CASE 17 — MIXED CONTENT
# ============================================================

def test_mixed_content_pdf(tmp_path):

    require_reportlab()

    from reportlab.platypus import (
        SimpleDocTemplate,
        Paragraph,
        Spacer,
        Table,
        TableStyle,
    )

    from reportlab.lib import colors
    from reportlab.lib.styles import (
        getSampleStyleSheet,
    )

    pdf_path = tmp_path / "mixed.pdf"

    styles = getSampleStyleSheet()

    document = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
    )

    table = Table(
        [
            ["Name", "Age"],
            ["Alice", "24"],
            ["Bob", "28"],
        ]
    )

    table.setStyle(
        TableStyle(
            [
                (
                    "GRID",
                    (0, 0),
                    (-1, -1),
                    1,
                    colors.black,
                )
            ]
        )
    )

    story = [
        Paragraph(
            "Mixed PDF Test",
            styles["Title"],
        ),
        Spacer(1, 20),
        Paragraph(
            "This is a normal paragraph.",
            styles["BodyText"],
        ),
        Spacer(1, 20),
        table,
        Spacer(1, 20),
        Paragraph(
            "End of document.",
            styles["BodyText"],
        ),
    ]

    document.build(story)

    result = extract_pdf(
        pdf_path,
        document_id="mixed-test",
    )

    assert_valid_result(result)

    assert len(result.elements) > 0

    assert_valid_ordering(result)


# ============================================================
# EDGE CASE 18 — REUSING SAME EXTRACTOR
# ============================================================

def test_same_extractor_multiple_pdfs(tmp_path):

    pdf1 = tmp_path / "first.pdf"
    pdf2 = tmp_path / "second.pdf"

    create_pdf(
        pdf1,
        [
            [
                "First document",
            ]
        ],
    )

    create_pdf(
        pdf2,
        [
            [
                "Second document",
            ]
        ],
    )

    extractor = PdfExtractor()

    result1 = extractor.extract(
        pdf1,
        document_id="doc-1",
        filename="first.pdf",
    )

    result2 = extractor.extract(
        pdf2,
        document_id="doc-2",
        filename="second.pdf",
    )

    assert_valid_result(result1)
    assert_valid_result(result2)

    assert_common_metadata(
        result1,
        "doc-1",
        "first.pdf",
    )

    assert_common_metadata(
        result2,
        "doc-2",
        "second.pdf",
    )

    assert_valid_ordering(result1)
    assert_valid_ordering(result2)


# ============================================================
# EDGE CASE 19 — DIFFERENT DOCUMENT IDS
# ============================================================

def test_document_metadata_isolated(tmp_path):

    pdf_path = tmp_path / "metadata.pdf"

    create_pdf(
        pdf_path,
        [
            [
                "Metadata isolation test",
            ]
        ],
    )

    result = extract_pdf(
        pdf_path,
        document_id="unique-document-id",
        filename="metadata.pdf",
    )

    assert_valid_result(result)

    assert_common_metadata(
        result,
        "unique-document-id",
        "metadata.pdf",
    )


# ============================================================
# EDGE CASE 20 — ORDER PRESERVATION
# ============================================================

def test_mixed_document_order_is_preserved(tmp_path):

    pdf_path = tmp_path / "order.pdf"

    create_pdf(
        pdf_path,
        [
            [
                "FIRST SECTION",
                "",
                "First paragraph",
                "",
                "SECOND SECTION",
                "",
                "Second paragraph",
                "",
                "THIRD SECTION",
            ]
        ],
    )

    result = extract_pdf(
        pdf_path,
        document_id="order-test",
    )

    assert_valid_result(result)

    assert_valid_ordering(result)

    texts = [
        element.text
        for element in result.elements
        if element.text
    ]

    assert len(texts) > 0


# ============================================================
# EDGE CASE 21 — PAGE METADATA
# ============================================================

def test_page_metadata_is_valid(tmp_path):

    pdf_path = tmp_path / "pages.pdf"

    create_pdf(
        pdf_path,
        [
            ["Page One"],
            ["Page Two"],
            ["Page Three"],
        ],
    )

    result = extract_pdf(
        pdf_path,
        document_id="page-test",
    )

    assert_valid_result(result)

    for element in result.elements:

        page = element.metadata.get(
            "page"
        )

        if page is not None:

            assert isinstance(
                page,
                int,
            )

            assert page >= 1


# ============================================================
# EDGE CASE 22 — SOURCE FILE IS NOT MODIFIED
# ============================================================

def test_pdf_source_file_not_modified(tmp_path):

    pdf_path = tmp_path / "readonly.pdf"

    create_pdf(
        pdf_path,
        [
            [
                "Read only PDF test",
            ]
        ],
    )

    before_size = pdf_path.stat().st_size

    extractor = PdfExtractor()

    extractor.extract(
        pdf_path,
        document_id="readonly",
        filename="readonly.pdf",
    )

    after_size = pdf_path.stat().st_size

    assert before_size == after_size


# ============================================================
# EDGE CASE 23 — MISSING FILE
# ============================================================

def test_missing_pdf():

    extractor = PdfExtractor()

    missing_path = Path(
        "this_file_does_not_exist_123456.pdf"
    )

    with pytest.raises(
        (FileNotFoundError, OSError, Exception)
    ):
        extractor.extract(
            missing_path,
            document_id="missing",
            filename="missing.pdf",
        )


# ============================================================
# EDGE CASE 24 — INVALID PDF
# ============================================================

def test_invalid_pdf(tmp_path):

    invalid_pdf = (
        tmp_path / "invalid.pdf"
    )

    invalid_pdf.write_text(
        "This is not a PDF.",
        encoding="utf-8",
    )

    extractor = PdfExtractor()

    with pytest.raises(Exception):
        extractor.extract(
            invalid_pdf,
            document_id="invalid",
            filename="invalid.pdf",
        )


# ============================================================
# EDGE CASE 25 — EMPTY TABLE CELLS + METADATA
# ============================================================

def test_empty_table_cells_metadata(tmp_path):

    pdf_path = tmp_path / "empty_table.pdf"

    create_table_pdf(
        pdf_path,
        [
            ["Name", "Email", "Phone"],
            ["Alice", "", "123"],
            ["", "bob@example.com", ""],
            ["Charlie", "charlie@example.com", "456"],
        ],
    )

    result = extract_pdf(
        pdf_path,
        document_id="empty-table",
    )

    assert_valid_result(result)

    tables = elements_of_type(
        result,
        ElementType.TABLE,
    )

    for table in tables:

        cells = table.metadata.get(
            "cells"
        )

        if cells is None:
            continue

        for row in cells:

            assert isinstance(
                row,
                list,
            )


# ============================================================
# EDGE CASE 26 — ALL ELEMENTS HAVE TEXT OR VALID IMAGE STATE
# ============================================================

def test_element_text_integrity(tmp_path):

    pdf_path = tmp_path / "text-integrity.pdf"

    create_pdf(
        pdf_path,
        [
            [
                "Text integrity test",
                "Another line",
            ]
        ],
    )

    result = extract_pdf(
        pdf_path,
        document_id="text-integrity",
    )

    assert_valid_result(result)

    for element in result.elements:

        if element.element_type == ElementType.IMAGE:
            continue

        assert element.text is not None

        assert isinstance(
            element.text,
            str,
        )


# ============================================================
# EDGE CASE 27 — SUPPORTED ELEMENT TYPES ONLY
# ============================================================

def test_only_supported_element_types(tmp_path):

    pdf_path = tmp_path / "element-types.pdf"

    create_pdf(
        pdf_path,
        [
            [
                "Heading-like text",
                "",
                "Normal paragraph",
                "",
                "Another paragraph",
            ]
        ],
    )

    result = extract_pdf(
        pdf_path,
        document_id="types",
    )

    assert_valid_result(result)

    supported_types = {
        ElementType.HEADING,
        ElementType.PARAGRAPH,
        ElementType.LIST,
        ElementType.TABLE,
        ElementType.CODE_BLOCK,
        ElementType.IMAGE,
    }

    for element in result.elements:

        assert element.element_type in (
            supported_types
        )


# ============================================================
# EDGE CASE 28 — TABLE MARKDOWN EXISTS
# ============================================================

def test_table_markdown_exists(tmp_path):

    pdf_path = tmp_path / "markdown_table.pdf"

    create_table_pdf(
        pdf_path,
        [
            ["Name", "Age"],
            ["Alice", "24"],
            ["Bob", "28"],
        ],
    )

    result = extract_pdf(
        pdf_path,
        document_id="markdown-table",
    )

    assert_valid_result(result)

    tables = elements_of_type(
        result,
        ElementType.TABLE,
    )

    for table in tables:

        markdown = table.metadata.get(
            "markdown"
        )

        if markdown is not None:

            assert isinstance(
                markdown,
                str,
            )

            assert markdown.strip() != ""


# ============================================================
# EDGE CASE 29 — TABLE INDEX STARTS FROM ZERO
# ============================================================

def test_table_index_starts_from_zero(tmp_path):

    pdf_path = tmp_path / "index_zero.pdf"

    create_table_pdf(
        pdf_path,
        [
            ["A", "B"],
            ["1", "2"],
        ],
    )

    result = extract_pdf(
        pdf_path,
        document_id="index-zero",
    )

    assert_valid_result(result)

    tables = elements_of_type(
        result,
        ElementType.TABLE,
    )

    if tables:

        first_index = tables[0].metadata.get(
            "table_index"
        )

        assert first_index == 0


# ============================================================
# EDGE CASE 30 — TABLE ID FORMAT
# ============================================================

def test_table_id_format(tmp_path):

    pdf_path = tmp_path / "table_id.pdf"

    create_table_pdf(
        pdf_path,
        [
            ["A", "B"],
            ["1", "2"],
        ],
    )

    result = extract_pdf(
        pdf_path,
        document_id="format-test",
    )

    assert_valid_result(result)

    tables = elements_of_type(
        result,
        ElementType.TABLE,
    )

    if tables:

        table = tables[0]

        table_id = table.metadata.get(
            "table_id"
        )

        assert table_id is not None

        assert table_id.startswith(
            "format-test-table-"
        )


# ============================================================
# EDGE CASE 31 — CODE METADATA
# ============================================================

def test_code_metadata(tmp_path):

    pdf_path = tmp_path / "code_metadata.pdf"

    create_pdf(
        pdf_path,
        [
            [
                "def test_function():",
                "    return True",
            ]
        ],
    )

    result = extract_pdf(
        pdf_path,
        document_id="code-metadata",
    )

    assert_valid_result(result)

    codes = elements_of_type(
        result,
        ElementType.CODE_BLOCK,
    )

    for code in codes:

        assert code.text is not None

        assert code.text.strip() != ""

        assert code.metadata.get(
            "page"
        ) is not None

        assert code.metadata.get(
            "source"
        ) == "docling"


# ============================================================
# EDGE CASE 32 — LARGE MULTI-PAGE DOCUMENT
# ============================================================

def test_large_multi_page_pdf(tmp_path):

    pages = []

    for page_number in range(20):

        pages.append(
            [
                f"Page {page_number + 1}",
                "This is test content.",
                "Another line of content.",
                "PDF extraction stress test.",
            ]
        )

    pdf_path = tmp_path / "large.pdf"

    create_pdf(
        pdf_path,
        pages,
    )

    result = extract_pdf(
        pdf_path,
        document_id="large-pdf",
    )

    assert_valid_result(result)

    assert len(result.elements) > 0

    assert_valid_ordering(result)


# ============================================================
# EDGE CASE 33 — REPEATED EXTRACTION
# ============================================================

def test_repeated_extraction_same_pdf(tmp_path):

    pdf_path = tmp_path / "repeat.pdf"

    create_pdf(
        pdf_path,
        [
            [
                "Repeated extraction test",
            ]
        ],
    )

    extractor = PdfExtractor()

    result1 = extractor.extract(
        pdf_path,
        document_id="repeat-1",
        filename="repeat.pdf",
    )

    result2 = extractor.extract(
        pdf_path,
        document_id="repeat-2",
        filename="repeat.pdf",
    )

    assert_valid_result(result1)
    assert_valid_result(result2)

    assert_common_metadata(
        result1,
        "repeat-1",
        "repeat.pdf",
    )

    assert_common_metadata(
        result2,
        "repeat-2",
        "repeat.pdf",
    )

    assert_valid_ordering(result1)
    assert_valid_ordering(result2)


# ============================================================
# EDGE CASE 34 — DIFFERENT FILENAMES
# ============================================================

def test_filename_metadata(tmp_path):

    pdf_path = tmp_path / "actual_file.pdf"

    create_pdf(
        pdf_path,
        [
            [
                "Filename metadata test",
            ]
        ],
    )

    result = extract_pdf(
        pdf_path,
        document_id="filename-test",
        filename="custom-name.pdf",
    )

    assert_valid_result(result)

    for element in result.elements:

        assert element.metadata.get(
            "filename"
        ) == "custom-name.pdf"


# ============================================================
# EDGE CASE 35 — RESULT IS DETERMINISTIC
# ============================================================

def test_same_pdf_produces_same_structure(tmp_path):

    pdf_path = tmp_path / "deterministic.pdf"

    create_pdf(
        pdf_path,
        [
            [
                "Deterministic extraction",
                "Second line",
            ]
        ],
    )

    extractor = PdfExtractor()

    result1 = extractor.extract(
        pdf_path,
        document_id="deterministic",
        filename="deterministic.pdf",
    )

    result2 = extractor.extract(
        pdf_path,
        document_id="deterministic",
        filename="deterministic.pdf",
    )

    assert_valid_result(result1)
    assert_valid_result(result2)

    assert len(
        result1.elements
    ) == len(
        result2.elements
    )

    for first, second in zip(
        result1.elements,
        result2.elements,
    ):

        assert first.order_index == (
            second.order_index
        )

        assert first.element_type == (
            second.element_type
        )

        assert first.text == second.text