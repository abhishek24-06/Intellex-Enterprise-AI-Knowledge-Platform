from collections import Counter
from pathlib import Path

from app.services.extraction.docx_extractor import DocxExtractor


def test_extract_real_report_everything():

    # ------------------------------------------------------------
    # PATHS
    # ------------------------------------------------------------

    docx_path = Path(
        "tests/doc_test/report.docx"
    )

    output_path = Path(
        "tests/doc_test/report_extraction.txt"
    )

    # ------------------------------------------------------------
    # EXTRACT
    # ------------------------------------------------------------

    extractor = DocxExtractor()

    result = extractor.extract(
        str(docx_path),
        document_id="real-report",
        filename=docx_path.name,
    )

    # ------------------------------------------------------------
    # BASIC VALIDATION
    # ------------------------------------------------------------

    assert result is not None
    assert result.elements

    # ------------------------------------------------------------
    # ELEMENT TYPE COUNTS
    # ------------------------------------------------------------

    counts = Counter(
        element.element_type
        for element in result.elements
    )

    # ------------------------------------------------------------
    # WRITE COMPLETE EXTRACTION
    # ------------------------------------------------------------

    with open(
        output_path,
        "w",
        encoding="utf-8",
    ) as file:

        file.write("=" * 100 + "\n")
        file.write("REAL DOCX EXTRACTION RESULT\n")
        file.write("=" * 100 + "\n\n")

        file.write(
            f"Document: {docx_path}\n"
        )

        file.write(
            f"Total elements: {len(result.elements)}\n\n"
        )

        file.write("-" * 100 + "\n")
        file.write("ELEMENT TYPE SUMMARY\n")
        file.write("-" * 100 + "\n")

        for element_type, count in counts.items():

            file.write(
                f"{element_type}: {count}\n"
            )

        file.write("\n")

        file.write("=" * 100 + "\n")
        file.write("ALL EXTRACTED ELEMENTS\n")
        file.write("=" * 100 + "\n\n")

        # --------------------------------------------------------
        # WRITE EVERY ELEMENT
        # --------------------------------------------------------

        for number, element in enumerate(
            result.elements,
            start=1,
        ):

            file.write("\n")
            file.write("#" * 100 + "\n")
            file.write(
                f"ELEMENT {number}\n"
            )
            file.write("#" * 100 + "\n")

            file.write(
                f"Order Index : {element.order_index}\n"
            )

            file.write(
                f"Element Type: {element.element_type}\n"
            )

            file.write("\n")

            file.write("TEXT:\n")
            file.write("-" * 100 + "\n")
            file.write(
                element.text
            )
            file.write("\n")

            file.write("\n")

            file.write("METADATA:\n")
            file.write("-" * 100 + "\n")

            file.write(
                repr(element.metadata)
            )

            file.write("\n")

    # ------------------------------------------------------------
    # CONSOLE SUMMARY
    # ------------------------------------------------------------

    print("\n")
    print("=" * 80)
    print("REAL DOCX EXTRACTION TEST PASSED")
    print("=" * 80)

    print(
        f"Document : {docx_path}"
    )

    print(
        f"Output   : {output_path}"
    )

    print(
        f"Elements : {len(result.elements)}"
    )

    print("\nElement Types:")

    for element_type, count in counts.items():

        print(
            f"  {element_type}: {count}"
        )

    print("=" * 80)