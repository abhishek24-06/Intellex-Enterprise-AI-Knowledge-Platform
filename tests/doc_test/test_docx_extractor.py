from pathlib import Path

from app.services.extraction.docx_extractor import DocxExtractor

extractor = DocxExtractor()

result = extractor.extract("tests/doc_test/report.docx")

output_path = Path("tests/doc_test/docx_output.txt")

with open(output_path, "w", encoding="utf-8") as f:

    f.write("=" * 80 + "\n")
    f.write(f"Total Elements: {len(result.elements)}\n")
    f.write("=" * 80 + "\n\n")

    for i, element in enumerate(result.elements, start=1):

        f.write(f"Element {i}\n")
        f.write(f"Type     : {element.element_type}\n")
        f.write(f"Text     :\n{element.text}\n")
        f.write(f"Metadata : {element.metadata}\n")
        f.write("=" * 80 + "\n\n")

print(f"Output saved to: {output_path}")