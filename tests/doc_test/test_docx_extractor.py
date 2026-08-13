from app.services.extraction.docx_extractor import DocxExtractor
from app.enums.element_type import ElementType


def test_extract_docx_code():

    extractor = DocxExtractor()

    result = extractor.extract(
        "tests/doc_test/code.docx",
        document_id="code-test",
        filename="code.docx",
    )

    # ------------------------------------------------------------
    # CODE VALIDATION
    # ------------------------------------------------------------

    codes = [
        element
        for element in result.elements
        if element.element_type == ElementType.CODE_BLOCK
    ]

    assert len(codes) == 4, (
        f"Expected 4 CODE_BLOCK elements, found {len(codes)}"
    )

    for code in codes:
        assert code.text.strip() != ""
        assert code.metadata.get("document_id") == "code-test"
        assert code.metadata.get("filename") == "code.docx"
        assert code.metadata.get("source") == "docx"
        assert code.metadata.get("detected_via") in {"style", "font"}

    # ------------------------------------------------------------
    # WRITE EXTRACTION OUTPUT
    # ------------------------------------------------------------

    output_path = "tests/doc_test/extracted_code.txt"

    with open(output_path, "w", encoding="utf-8") as file:

        for element in result.elements:

            file.write("=" * 80 + "\n")
            file.write(f"Order Index: {element.order_index}\n")
            file.write(f"Element Type: {element.element_type}\n")
            file.write(f"Text:\n{element.text}\n")
            file.write(f"Metadata: {element.metadata}\n")
            file.write("\n")

    print("\n" + "=" * 80)
    print("DOCX CODE EXTRACTION TEST PASSED")
    print("=" * 80)
    print(f"DOCX     : tests/doc_test/code.docx")
    print(f"TXT      : {output_path}")
    print(f"Elements : {len(result.elements)}")
    print(f"Code     : {len(codes)}")
    print("=" * 80)