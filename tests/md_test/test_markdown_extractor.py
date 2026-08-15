from pathlib import Path

from app.services.extraction.markdown_extractor import MarkdownExtractor


def test_extract_real_sample_markdown():

    file_path = Path("tests/md_test/sample.md")

    output_path = Path(
        "tests/md_test/md_extraction_result.txt"
    )

    extractor = MarkdownExtractor()

    result = extractor.extract(file_path)

    # ---------------------------------------------------------
    # Write extracted elements to TXT
    # ---------------------------------------------------------

    with open(
        output_path,
        "w",
        encoding="utf-8",
    ) as file:

        file.write(
            "========== EXTRACTED ELEMENTS ==========\n\n"
        )

        for element in result.elements:

            file.write(
                f"Order Index : {element.order_index}\n"
            )

            file.write(
                f"Type        : {element.element_type}\n"
            )

            file.write(
                f"Text        : {element.text!r}\n"
            )

            file.write(
                f"Metadata    : {element.metadata}\n"
            )

            file.write(
                "-" * 80 + "\n"
            )

    # ---------------------------------------------------------
    # Assertions
    # ---------------------------------------------------------

    assert result is not None
    assert result.elements

    print(
        f"\nExtraction written to: {output_path}"
    )