from pathlib import Path

from app.services.extraction.markdown_extractor import MarkdownExtractor


def test_extract_real_sample_markdown():

    file_path = Path("tests/md_test/sample.md")

    extractor = MarkdownExtractor()

    result = extractor.extract(file_path)

    print("\n========== EXTRACTED ELEMENTS ==========\n")

    for element in result.elements:
        print(f"Order Index : {element.order_index}")
        print(f"Type        : {element.element_type}")
        print(f"Text        : {element.text!r}")
        print(f"Metadata    : {element.metadata}")
        print("-" * 80)

    assert result is not None
    assert result.elements