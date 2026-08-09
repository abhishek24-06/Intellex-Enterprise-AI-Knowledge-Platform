from app.dto.extracted_element import ExtractedElement
from app.dto.extraction_result import ExtractionResult
from app.enums.element_type import ElementType
from app.services.chunking.structure_builder.structure_builder import DocumentStructureBuilder


def make_heading(text, level):
    return ExtractedElement(
        order_index=0,
        text=text,
        element_type=ElementType.HEADING,
        metadata={"level": level},
    )


def make_paragraph(text):
    return ExtractedElement(
        order_index=0,
        text=text,
        element_type=ElementType.PARAGRAPH,
        metadata={},
    )


def make_table(text="Table"):
    return ExtractedElement(
        order_index=0,
        text=text,
        element_type=ElementType.TABLE,
        metadata={},
    )


def make_result(elements):
    return ExtractionResult(elements=elements)


# ============================================================
# 1. EMPTY DOCUMENT
# ============================================================

def test_empty_document():

    result = make_result([])

    tree = DocumentStructureBuilder().build(result)

    assert tree.root.element is None
    assert tree.root.children == []


# ============================================================
# 2. SINGLE HEADING
# ============================================================

def test_single_heading():

    elements = [
        make_heading("Introduction", 1),
        make_paragraph("Introduction content."),
    ]

    tree = DocumentStructureBuilder().build(
        make_result(elements)
    )

    root = tree.root

    assert len(root.children) == 1 

    heading_node = root.children[0]

    assert heading_node.element.text == "Introduction"
    assert heading_node.element.metadata["level"] == 1

    assert len(heading_node.children) == 1
    assert heading_node.children[0].element.text == "Introduction content."

    assert heading_node.parent is root


# ============================================================
# 3. NESTED HEADINGS
# ============================================================

def test_nested_headings():

    elements = [
        make_heading("Introduction", 1),
        make_heading("Background", 2),
        make_paragraph("Background content."),
        make_heading("Architecture", 2),
        make_paragraph("Architecture content."),
    ]

    tree = DocumentStructureBuilder().build(
        make_result(elements)
    )

    root = tree.root

    introduction = root.children[0]

    assert introduction.element.text == "Introduction"

    assert len(introduction.children) == 2

    background = introduction.children[0]
    architecture = introduction.children[1]

    assert background.element.text == "Background"
    assert architecture.element.text == "Architecture"

    assert background.parent is introduction
    assert architecture.parent is introduction


# ============================================================
# 4. DEEP HIERARCHY
# ============================================================

def test_deep_hierarchy():

    elements = [
        make_heading("Chapter 1", 1),
        make_heading("Section 1.1", 2),
        make_heading("Section 1.1.1", 3),
        make_paragraph("Deep content."),
    ]

    tree = DocumentStructureBuilder().build(
        make_result(elements)
    )

    chapter = tree.root.children[0]
    section = chapter.children[0]
    subsection = section.children[0]

    assert chapter.element.text == "Chapter 1"
    assert section.element.text == "Section 1.1"
    assert subsection.element.text == "Section 1.1.1"

    assert subsection.children[0].element.text == "Deep content."


# ============================================================
# 5. SIBLING HEADINGS
# ============================================================

def test_sibling_headings():

    elements = [
        make_heading("Section 1", 1),
        make_paragraph("Section 1 content."),
        make_heading("Section 2", 1),
        make_paragraph("Section 2 content."),
    ]

    tree = DocumentStructureBuilder().build(
        make_result(elements)
    )

    root = tree.root

    assert len(root.children) == 2

    section1 = root.children[0]
    section2 = root.children[1]

    assert section1.element.text == "Section 1"
    assert section2.element.text == "Section 2"

    assert section1.children[0].element.text == "Section 1 content."
    assert section2.children[0].element.text == "Section 2 content."

    assert section1.parent is root
    assert section2.parent is root


# ============================================================
# 6. RETURNING FROM CHILD TO PARENT
# ============================================================

def test_return_to_parent_heading():

    elements = [
        make_heading("Chapter", 1),
        make_heading("Section", 2),
        make_paragraph("Section content."),
        make_heading("Next Chapter", 1),
        make_paragraph("Next chapter content."),
    ]

    tree = DocumentStructureBuilder().build(
        make_result(elements)
    )

    root = tree.root

    assert len(root.children) == 2

    chapter = root.children[0]
    next_chapter = root.children[1]

    assert chapter.element.text == "Chapter"
    assert next_chapter.element.text == "Next Chapter"

    section = chapter.children[0]

    assert section.element.text == "Section"
    assert section.children[0].element.text == "Section content."

    assert next_chapter.children[0].element.text == "Next chapter content."


# ============================================================
# 7. PREAMBLE BEFORE FIRST HEADING
# ============================================================

def test_preamble_before_first_heading():

    elements = [
        make_paragraph("This is the first paragraph."),
        make_paragraph("This is the second paragraph."),
        make_heading("Introduction", 1),
        make_paragraph("Introduction content."),
    ]

    tree = DocumentStructureBuilder().build(
        make_result(elements)
    )

    root = tree.root

    # Preamble stays directly under synthetic root
    assert len(root.children) == 3

    assert root.children[0].element.text == "This is the first paragraph."
    assert root.children[1].element.text == "This is the second paragraph."

    # Heading is also directly under root
    introduction = root.children[2]

    assert introduction.element.text == "Introduction"

    # Content after heading belongs to heading
    assert len(introduction.children) == 1
    assert introduction.children[0].element.text == "Introduction content."


# ============================================================
# 8. TABLE STAYS UNDER CURRENT SECTION
# ============================================================

def test_table_stays_under_current_section():

    elements = [
        make_heading("Architecture", 1),
        make_paragraph("Architecture description."),
        make_table("Component | Technology"),
        make_paragraph("More architecture details."),
    ]

    tree = DocumentStructureBuilder().build(
        make_result(elements)
    )

    architecture = tree.root.children[0]

    assert len(architecture.children) == 3

    assert architecture.children[0].element.element_type == ElementType.PARAGRAPH
    assert architecture.children[1].element.element_type == ElementType.TABLE
    assert architecture.children[2].element.element_type == ElementType.PARAGRAPH


# ============================================================
# 9. MULTIPLE TABLES UNDER SAME SECTION
# ============================================================

def test_multiple_tables_under_same_section():

    elements = [
        make_heading("Data", 1),
        make_table("Table 1"),
        make_table("Table 2"),
        make_table("Table 3"),
    ]

    tree = DocumentStructureBuilder().build(
        make_result(elements)
    )

    data = tree.root.children[0]

    assert len(data.children) == 3

    assert data.children[0].element.text == "Table 1"
    assert data.children[1].element.text == "Table 2"
    assert data.children[2].element.text == "Table 3"


# ============================================================
# 10. MIXED DOCUMENT
# ============================================================

def test_mixed_document():

    elements = [
        make_paragraph("Preamble."),
        make_heading("Introduction", 1),
        make_paragraph("Intro content."),
        make_heading("Architecture", 2),
        make_paragraph("Architecture content."),
        make_table("Architecture table"),
        make_heading("Implementation", 2),
        make_paragraph("Implementation content."),
        make_heading("Conclusion", 1),
        make_paragraph("Conclusion content."),
    ]

    tree = DocumentStructureBuilder().build(
        make_result(elements)
    )

    root = tree.root

    # Preamble + two H1-level sections
    assert len(root.children) == 3

    assert root.children[0].element.text == "Preamble."

    introduction = root.children[1]
    conclusion = root.children[2]

    assert introduction.element.text == "Introduction"
    assert conclusion.element.text == "Conclusion"

    # H2 sections belong to Introduction
    assert len(introduction.children) == 3

    assert introduction.children[0].element.text == "Intro content."

    architecture = introduction.children[1]
    implementation = introduction.children[2]

    assert architecture.element.text == "Architecture"
    assert implementation.element.text == "Implementation"

    # Architecture contains paragraph + table
    assert len(architecture.children) == 2

    assert architecture.children[0].element.text == "Architecture content."
    assert architecture.children[1].element.element_type == ElementType.TABLE

    # Implementation contains its paragraph
    assert len(implementation.children) == 1
    assert implementation.children[0].element.text == "Implementation content."

    # Conclusion is back at root level
    assert len(conclusion.children) == 1
    assert conclusion.children[0].element.text == "Conclusion content."