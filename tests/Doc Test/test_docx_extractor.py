from app.services.extraction.docx_extractor import DocxExtractor

extractor = DocxExtractor()

result = extractor.extract("tests/intellex_docx_extractor_test.docx")   # <-- path to your test document

print("=" * 80)
print(f"Total Elements: {len(result.elements)}")
print("=" * 80)

for i, element in enumerate(result.elements, start=1):
    print(f"\nElement {i}")
    print(f"Type     : {element.element_type}")
    print(f"Text     : {element.text}")
    print(f"Metadata : {element.metadata}")