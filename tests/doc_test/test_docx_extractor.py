from app.services.extraction.docx_extractor import DocxExtractor


extractor = DocxExtractor()

result = extractor.extract(
    "tests/doc_test/report.docx",
    document_id="real-report",
    filename="report.docx",
)

with open(
    "tests/doc_test/extracted_report.txt",
    "w",
    encoding="utf-8"
) as file:

    for element in result.elements:

        file.write("=" * 80 + "\n")
        file.write(f"Order Index: {element.order_index}\n")
        file.write(f"Element Type: {element.element_type}\n")
        file.write(f"Text:\n{element.text}\n")
        file.write(f"Metadata: {element.metadata}\n")
        file.write("\n")

print("Extraction complete.")
print("Saved to: tests/doc_test/extracted_report.txt")