import os
from pathlib import Path

os.environ["TORCH_COMPILE_DISABLE"] = "1"

from app.services.extraction.pdf.pdf_extractor import PdfExtractor


def main():

    pdf_path = Path("tests/pdf_test/report.pdf")

    extractor = PdfExtractor()

    result = extractor.extract(pdf_path)

    output_path = Path("tests/pdf_test/extracted_output.txt")

    with open(output_path, "w", encoding="utf-8") as f:

        f.write(f"Extracted {len(result.elements)} elements\n\n")

        for i, element in enumerate(result.elements, start=1):

            f.write("=" * 80 + "\n")
            f.write(f"Element {i}\n")
            f.write(f"Type      : {element.element_type}\n")
            f.write(f"Text      :\n{element.text}\n")
            f.write(f"Metadata  : {element.metadata}\n\n")

    print(f"Output saved to: {output_path}")


if __name__ == "__main__":
    main()