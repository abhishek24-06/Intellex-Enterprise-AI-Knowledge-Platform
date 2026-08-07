from pathlib import Path

from app.services.extraction.txt_extractor import TxtExtractor


def main():

    extractor = TxtExtractor()

    result = extractor.extract(
        "tests/txt_test/sample.txt"
    )

    output_file = Path("tests/txt_test/output.txt")

    with open(output_file, "w", encoding="utf-8") as f:

        f.write("=" * 80 + "\n")
        f.write(f"Extracted {len(result.elements)} elements\n")
        f.write("=" * 80 + "\n\n")

        for element in result.elements:

            f.write("=" * 80 + "\n")
            f.write(f"Order     : {element.order_index}\n")
            f.write(f"Type      : {element.element_type}\n")
            f.write("Text      :\n")
            f.write(element.text + "\n")
            f.write(f"Metadata  : {element.metadata}\n\n")

    print(f"Output written to {output_file}")


if __name__ == "__main__":
    main()