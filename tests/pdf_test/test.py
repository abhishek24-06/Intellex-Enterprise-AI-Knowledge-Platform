import os
from pathlib import Path

os.environ["TORCH_COMPILE_DISABLE"] = "1"

from app.services.extraction.pdf.pdf_extractor import PdfExtractor
from app.enums.element_type import ElementType


def test_extract_real_pdf():

    # ============================================================
    # INPUT / OUTPUT PATHS
    # ============================================================

    test_dir = Path(__file__).parent

    # Real PDF
    pdf_path = test_dir / "report.pdf"

    # Extracted output
    output_path = test_dir / "extracted_doc.txt"

    # Make sure the PDF actually exists
    assert pdf_path.exists(), f"PDF not found: {pdf_path}"

    # ============================================================
    # RUN PDF EXTRACTOR
    # ============================================================

    extractor = PdfExtractor()

    result = extractor.extract(
        pdf_path,
        document_id="real-pdf-test",
        filename=pdf_path.name,
    )

    # ============================================================
    # BASIC VALIDATION
    # ============================================================

    assert result is not None
    assert result.elements is not None

    elements = result.elements

    assert len(elements) > 0, "PDF extraction returned no elements"

    # ============================================================
    # COUNT ELEMENT TYPES
    # ============================================================

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

    # ============================================================
    # WRITE EVERYTHING TO TXT
    # ============================================================

    with output_path.open("w", encoding="utf-8") as f:

        f.write("=" * 100 + "\n")
        f.write("REAL PDF EXTRACTION TEST RESULT\n")
        f.write("=" * 100 + "\n\n")

        f.write(f"Input PDF     : {pdf_path}\n")
        f.write(f"Output TXT    : {output_path}\n")
        f.write(f"Total elements: {len(elements)}\n\n")

        # --------------------------------------------------------
        # ELEMENT COUNTS
        # --------------------------------------------------------

        f.write("=" * 100 + "\n")
        f.write("ELEMENT COUNTS\n")
        f.write("=" * 100 + "\n\n")

        f.write(f"Headings   : {heading_count}\n")
        f.write(f"Paragraphs : {paragraph_count}\n")
        f.write(f"Lists      : {list_count}\n")
        f.write(f"Tables     : {table_count}\n")
        f.write(f"Code       : {code_count}\n")
        f.write(f"Images     : {image_count}\n\n")

        # --------------------------------------------------------
        # ALL EXTRACTED ELEMENTS
        # --------------------------------------------------------

        f.write("=" * 100 + "\n")
        f.write("EXTRACTED ELEMENTS\n")
        f.write("=" * 100 + "\n\n")

        for element in elements:

            f.write("-" * 100 + "\n")

            f.write(f"Order Index : {element.order_index}\n")
            f.write(f"Element Type: {element.element_type}\n")

            # ----------------------------------------------------
            # METADATA
            # ----------------------------------------------------

            f.write(f"Metadata    : {element.metadata}\n\n")

            # ----------------------------------------------------
            # TABLE INFORMATION
            # ----------------------------------------------------

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

            # ----------------------------------------------------
            # TEXT
            # ----------------------------------------------------

            f.write("TEXT:\n")

            text = getattr(element, "text", None)

            if text:
                f.write(str(text))
            else:
                f.write("[NO TEXT]")

            f.write("\n\n")

            # ----------------------------------------------------
            # TABLE MARKDOWN
            # ----------------------------------------------------

            if element.element_type == ElementType.TABLE:

                markdown = element.metadata.get("markdown")

                if markdown:

                    f.write("TABLE MARKDOWN:\n")
                    f.write("-" * 50 + "\n")
                    f.write(str(markdown))
                    f.write("\n\n")

    # ============================================================
    # VALIDATION ASSERTIONS
    # ============================================================

    # The extractor must return something
    assert len(elements) > 0

    # ------------------------------------------------------------
    # ORDER INDEX VALIDATION
    # ------------------------------------------------------------

    # Every element must have an order index
    for element in elements:

        assert element.order_index is not None

    # Order indices should be unique
    order_indices = [
        element.order_index
        for element in elements
    ]

    assert len(order_indices) == len(set(order_indices)), (
        "Duplicate order_index detected"
    )

    # Order indices should be sorted in document order
    assert order_indices == sorted(order_indices), (
        "Elements are not in order_index order"
    )

    # ------------------------------------------------------------
    # TABLE VALIDATION
    # ------------------------------------------------------------

    tables = [
        element
        for element in elements
        if element.element_type == ElementType.TABLE
    ]

    if tables:

        # Get table_index from metadata
        table_indices = [
            table.metadata.get("table_index")
            for table in tables
        ]

        # Every table must have table_index
        assert all(
            index is not None
            for index in table_indices
        ), (
            "One or more tables are missing table_index"
        )

        # Table indices must be unique
        assert len(table_indices) == len(set(table_indices)), (
            "Duplicate table_index detected"
        )

        # Table indices should be sequential
        expected_table_indices = list(
            range(len(tables))
        )

        assert sorted(table_indices) == expected_table_indices, (
            f"Invalid table_index sequence: "
            f"{table_indices}"
        )

        # --------------------------------------------------------
        # TABLE ID VALIDATION
        # --------------------------------------------------------

        table_ids = [
            table.metadata.get("table_id")
            for table in tables
        ]

        # Every table must have a table_id
        assert all(
            table_id is not None
            for table_id in table_ids
        ), (
            "One or more tables are missing table_id"
        )

        # Table IDs must be unique
        assert len(table_ids) == len(set(table_ids)), (
            "Duplicate table_id detected"
        )

        # --------------------------------------------------------
        # TABLE DIMENSION VALIDATION
        # --------------------------------------------------------

        for table in tables:

            metadata = table.metadata

            n_rows = metadata.get("n_rows")
            n_cols = metadata.get("n_cols")

            assert n_rows is not None, (
                f"Table {metadata.get('table_index')} "
                f"is missing n_rows"
            )

            assert n_cols is not None, (
                f"Table {metadata.get('table_index')} "
                f"is missing n_cols"
            )

            assert n_rows > 0, (
                f"Table {metadata.get('table_index')} "
                f"has invalid row count: {n_rows}"
            )

            assert n_cols > 0, (
                f"Table {metadata.get('table_index')} "
                f"has invalid column count: {n_cols}"
            )

        # ------------------------------------------------------------
        # CODE VALIDATION
        # ------------------------------------------------------------
        
        codes = [
            element
            for element in elements
            if element.element_type == ElementType.CODE_BLOCK
        ]
        
        assert len(codes) > 0, (
            "PDF contains no extracted CODE_BLOCK elements"
        )
        
        for code in codes:
            assert code.text is not None
            assert code.text.strip() != ""
        
            assert code.metadata.get("page") is not None
            assert code.metadata.get("source") == "docling"

    # ============================================================
    # FINAL SUCCESS MESSAGE
    # ============================================================

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