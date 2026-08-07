from app.services.extraction.markdown_extractor import MarkdownExtractor

extractor = MarkdownExtractor()

result = extractor.extract("tests/md_test/sample.md")

print("=" * 80)
print(f"Total Elements: {len(result.elements)}")
print("=" * 80)

for i, element in enumerate(result.elements, start=1):

    print(f"\nElement {i}")
    print(f"Order    : {element.order_index}")
    print(f"Type     : {element.element_type}")
    print(f"Text     : {element.text}")
    print(f"Metadata : {element.metadata}")