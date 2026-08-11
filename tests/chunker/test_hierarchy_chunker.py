from app.services.chunking.hierarchy.hierarchy_chunker import HierarchyChunker
from app.dto.document_node import DocumentNode
from app.dto.document_tree import DocumentTree
from app.dto.extracted_element import ExtractedElement
from app.enums.element_type import ElementType


# ============================================================
# Helpers
# ============================================================

def make_element(element_type, text, order_index=0, metadata=None):
    return ExtractedElement(
        order_index=order_index,
        text=text,
        element_type=element_type,
        metadata=metadata or {},
    )


def make_heading(text, level=1, order_index=0):
    return make_element(
        element_type=ElementType.HEADING,
        text=text,
        order_index=order_index,
        metadata={"level": level},
    )


def make_paragraph(text, order_index=0):
    return make_element(
        element_type=ElementType.PARAGRAPH,
        text=text,
        order_index=order_index,
    )


def make_table(text="Table", order_index=0):
    return make_element(
        element_type=ElementType.TABLE,
        text=text,
        order_index=order_index,
    )


def make_code(text="code()", order_index=0):
    return make_element(
        element_type=ElementType.CODE_BLOCK,
        text=text,
        order_index=order_index,
    )


def make_tree(elements):
    """
    Build a DocumentTree manually.

    This intentionally uses the same basic hierarchy behavior as the
    DocumentStructureBuilder so that these tests focus on HierarchyChunker.
    """

    root = DocumentNode(element=None)

    stack = [root]

    for element in elements:

        if element.element_type == ElementType.HEADING:

            level = element.metadata.get("level") or 1

            while (
                len(stack) > 1
                and (stack[-1].element.metadata.get("level") or 1) >= level
            ):
                stack.pop()

            node = DocumentNode(element=element)

            stack[-1].add_child(node)

            stack.append(node)

        else:

            stack[-1].add_child(
                DocumentNode(element=element)
            )

    return DocumentTree(root=root)


# ============================================================
# Basic behavior
# ============================================================

def test_empty_tree_returns_no_candidates():

    tree = make_tree([])

    candidates = HierarchyChunker().chunk(tree)

    assert candidates == []


def test_root_paragraph_creates_root_candidate():

    tree = make_tree([
        make_paragraph("First paragraph"),
        make_paragraph("Second paragraph"),
    ])

    candidates = HierarchyChunker().chunk(tree)

    assert len(candidates) == 1

    candidate = candidates[0]

    assert candidate.heading is None
    assert candidate.section_path == []

    assert candidate.text == (
        "First paragraph\n\n"
        "Second paragraph"
    )


def test_single_section_creates_one_candidate():

    tree = make_tree([
        make_heading("Introduction", 1),
        make_paragraph("This is the introduction."),
        make_paragraph("More introduction content."),
    ])

    candidates = HierarchyChunker().chunk(tree)

    assert len(candidates) == 1

    candidate = candidates[0]

    assert candidate.heading == "Introduction"

    assert candidate.section_path == [
        "Introduction"
    ]

    assert candidate.text == (
        "Section: Introduction\n\n"
        "This is the introduction.\n\n"
        "More introduction content."
    )


# ============================================================
# Hierarchy
# ============================================================

def test_nested_section_creates_separate_candidates():

    tree = make_tree([
        make_heading("Introduction", 1),
        make_paragraph("Introduction content."),

        make_heading("Background", 2),
        make_paragraph("Background content."),
    ])

    candidates = HierarchyChunker().chunk(tree)

    assert len(candidates) == 2

    introduction = candidates[0]
    background = candidates[1]

    assert introduction.heading == "Introduction"

    assert introduction.section_path == [
        "Introduction"
    ]

    assert background.heading == "Background"

    assert background.section_path == [
        "Introduction",
        "Background",
    ]


def test_sibling_sections_have_correct_paths():

    tree = make_tree([
        make_heading("Introduction", 1),
        make_paragraph("Intro content."),

        make_heading("Architecture", 1),
        make_paragraph("Architecture content."),

        make_heading("Conclusion", 1),
        make_paragraph("Conclusion content."),
    ])

    candidates = HierarchyChunker().chunk(tree)

    assert len(candidates) == 3

    assert candidates[0].section_path == [
        "Introduction"
    ]

    assert candidates[1].section_path == [
        "Architecture"
    ]

    assert candidates[2].section_path == [
        "Conclusion"
    ]


def test_deep_hierarchy_builds_full_breadcrumb():

    tree = make_tree([
        make_heading("System", 1),
        make_heading("Architecture", 2),
        make_heading("Backend", 3),
        make_paragraph("Backend implementation."),
    ])

    candidates = HierarchyChunker().chunk(tree)

    assert len(candidates) == 1

    candidate = candidates[0]

    assert candidate.heading == "Backend"

    assert candidate.section_path == [
        "System",
        "Architecture",
        "Backend",
    ]

    assert candidate.text == (
        "Section: System > Architecture > Backend\n\n"
        "Backend implementation."
    )


def test_deep_hierarchy_five_levels():

    tree = make_tree([
        make_heading("L1", 1),
        make_heading("L2", 2),
        make_heading("L3", 3),
        make_heading("L4", 4),
        make_heading("L5", 5),
        make_paragraph("Deep content."),
    ])

    candidates = HierarchyChunker().chunk(tree)

    assert len(candidates) == 1

    candidate = candidates[0]

    assert candidate.section_path == [
        "L1",
        "L2",
        "L3",
        "L4",
        "L5",
    ]

    assert candidate.text == (
        "Section: L1 > L2 > L3 > L4 > L5\n\n"
        "Deep content."
    )


def test_heading_level_jump():

    tree = make_tree([
        make_heading("Introduction", 1),
        make_heading("Details", 3),
        make_paragraph("Detailed content."),
    ])

    candidates = HierarchyChunker().chunk(tree)

    assert len(candidates) == 1

    assert candidates[0].section_path == [
        "Introduction",
        "Details",
    ]


def test_sibling_after_deep_child():

    tree = make_tree([
        make_heading("Root", 1),

        make_heading("Deep A", 2),

        make_heading("Deep B", 3),
        make_paragraph("Deep content."),

        make_heading("Sibling", 2),
        make_paragraph("Sibling content."),
    ])

    candidates = HierarchyChunker().chunk(tree)

    assert len(candidates) == 2

    assert candidates[0].section_path == [
        "Root",
        "Deep A",
        "Deep B",
    ]

    assert candidates[1].section_path == [
        "Root",
        "Sibling",
    ]


def test_parent_and_child_sections_are_both_processed():

    tree = make_tree([
        make_heading("Parent", 1),
        make_paragraph("Parent content."),

        make_heading("Child", 2),
        make_paragraph("Child content."),
    ])

    candidates = HierarchyChunker().chunk(tree)

    assert len(candidates) == 2

    assert candidates[0].heading == "Parent"

    assert candidates[0].section_path == [
        "Parent"
    ]

    assert candidates[1].heading == "Child"

    assert candidates[1].section_path == [
        "Parent",
        "Child",
    ]


# ============================================================
# Preamble
# ============================================================

def test_preamble_and_section_create_separate_candidates():

    tree = make_tree([
        make_paragraph("Document preamble."),

        make_heading("Introduction", 1),
        make_paragraph("Introduction content."),
    ])

    candidates = HierarchyChunker().chunk(tree)

    assert len(candidates) == 2

    preamble = candidates[0]
    introduction = candidates[1]

    assert preamble.heading is None
    assert preamble.section_path == []

    assert preamble.text == (
        "Document preamble."
    )

    assert introduction.heading == "Introduction"

    assert introduction.section_path == [
        "Introduction"
    ]


# ============================================================
# Breadcrumb tests
# ============================================================

def test_nested_section_includes_full_breadcrumb():

    tree = make_tree([
        make_heading("Features of Intellex", 1),
        make_heading("RAG Pipeline", 2),
        make_paragraph(
            "Intellex uses hybrid retrieval..."
        ),
    ])

    candidates = HierarchyChunker().chunk(tree)

    assert len(candidates) == 1

    candidate = candidates[0]

    assert candidate.section_path == [
        "Features of Intellex",
        "RAG Pipeline",
    ]

    assert candidate.text == (
        "Section: Features of Intellex > RAG Pipeline\n\n"
        "Intellex uses hybrid retrieval..."
    )


def test_top_level_section_uses_single_level_breadcrumb():

    tree = make_tree([
        make_heading("Introduction", 1),
        make_paragraph(
            "Intellex is an enterprise knowledge platform..."
        ),
    ])

    candidates = HierarchyChunker().chunk(tree)

    assert len(candidates) == 1

    candidate = candidates[0]

    assert candidate.section_path == [
        "Introduction",
    ]

    assert candidate.text == (
        "Section: Introduction\n\n"
        "Intellex is an enterprise knowledge platform..."
    )


def test_three_level_section_includes_full_breadcrumb():

    tree = make_tree([
        make_heading("Intellex", 1),
        make_heading("RAG", 2),
        make_heading("Hybrid Retrieval", 3),
        make_paragraph(
            "Uses BM25 and vector search..."
        ),
    ])

    candidates = HierarchyChunker().chunk(tree)

    assert len(candidates) == 1

    candidate = candidates[0]

    assert candidate.section_path == [
        "Intellex",
        "RAG",
        "Hybrid Retrieval",
    ]

    assert candidate.text == (
        "Section: Intellex > RAG > Hybrid Retrieval\n\n"
        "Uses BM25 and vector search..."
    )


# ============================================================
# Tables and code delegation
# ============================================================

def test_table_is_excluded_from_narrative_text():

    tree = make_tree([
        make_heading("Architecture", 1),

        make_paragraph("Before table."),

        make_table("Component | Technology"),

        make_paragraph("After table."),
    ])

    candidates = HierarchyChunker().chunk(tree)

    assert len(candidates) == 1

    candidate = candidates[0]

    assert "Before table." in candidate.text
    assert "After table." in candidate.text

    assert "Component | Technology" not in candidate.text


def test_code_is_excluded_from_narrative_text():

    tree = make_tree([
        make_heading("Implementation", 1),

        make_paragraph("Explanation before code."),

        make_code("print('hello')"),

        make_paragraph("Explanation after code."),
    ])

    candidates = HierarchyChunker().chunk(tree)

    assert len(candidates) == 1

    candidate = candidates[0]

    assert "Explanation before code." in candidate.text
    assert "Explanation after code." in candidate.text

    assert "print('hello')" not in candidate.text


def test_table_and_code_are_preserved_in_candidate_elements():

    paragraph1 = make_paragraph("Before.", 1)
    table = make_table("Table data", 2)
    paragraph2 = make_paragraph("After.", 3)
    code = make_code("print('hello')", 4)

    tree = make_tree([
        make_heading("Section", 1),
        paragraph1,
        table,
        paragraph2,
        code,
    ])

    candidates = HierarchyChunker().chunk(tree)

    assert len(candidates) == 1

    candidate = candidates[0]

    assert candidate.elements == [
        paragraph1,
        table,
        paragraph2,
        code,
    ]

    assert "Table data" not in candidate.text
    assert "print('hello')" not in candidate.text


def test_section_with_only_table_creates_candidate_for_delegation():

    table1 = make_table("Table 1")
    table2 = make_table("Table 2")

    tree = make_tree([
        make_heading("Data", 1),
        table1,
        table2,
    ])

    candidates = HierarchyChunker().chunk(tree)

    assert len(candidates) == 1

    candidate = candidates[0]

    assert candidate.section_path == ["Data"]
    assert candidate.text == "Section: Data"
    assert candidate.elements == [table1, table2]


def test_section_with_only_code_creates_candidate_for_delegation():

    code1 = make_code("print('one')")
    code2 = make_code("print('two')")

    tree = make_tree([
        make_heading("Code", 1),
        code1,
        code2,
    ])

    candidates = HierarchyChunker().chunk(tree)

    assert len(candidates) == 1

    candidate = candidates[0]

    assert candidate.section_path == ["Code"]
    assert candidate.text == "Section: Code"
    assert candidate.elements == [code1, code2]


def test_multiple_tables_do_not_create_multiple_narrative_candidates():

    tree = make_tree([
        make_heading("Data", 1),

        make_paragraph("Data description."),

        make_table("Table 1"),
        make_table("Table 2"),
        make_table("Table 3"),
    ])

    candidates = HierarchyChunker().chunk(tree)

    assert len(candidates) == 1

    candidate = candidates[0]

    assert candidate.text == (
        "Section: Data\n\n"
        "Data description."
    )

    assert len(candidate.elements) == 4

    assert candidate.elements[0].element_type == (
        ElementType.PARAGRAPH
    )

    assert all(
        element.element_type == ElementType.TABLE
        for element in candidate.elements[1:]
    )


def test_many_delegated_elements_between_paragraphs():

    tree = make_tree([
        make_heading("Data", 1),

        make_paragraph("Before."),

        make_table("Table 1"),
        make_table("Table 2"),

        make_code("code1()"),
        make_code("code2()"),

        make_paragraph("After."),
    ])

    candidates = HierarchyChunker().chunk(tree)

    assert len(candidates) == 1

    candidate = candidates[0]

    assert candidate.text == (
        "Section: Data\n\n"
        "Before.\n\n"
        "After."
    )

    assert len(candidate.elements) == 6


# ============================================================
# Parent / child delegation edge cases
# ============================================================

def test_parent_only_table_child_has_narrative():

    parent_table = make_table("Parent table")

    tree = make_tree([
        make_heading("Parent", 1),
        parent_table,
        make_heading("Child", 2),
        make_paragraph("Child content."),
    ])

    candidates = HierarchyChunker().chunk(tree)

    assert len(candidates) == 2

    parent = candidates[0]
    child = candidates[1]

    assert parent.section_path == ["Parent"]
    assert parent.text == "Section: Parent"
    assert parent.elements == [parent_table]

    assert child.section_path == ["Parent", "Child"]
    assert child.text == (
        "Section: Parent > Child\n\n"
        "Child content."
    )


def test_child_only_table_creates_child_candidate_for_delegation():

    child_table = make_table("Child table")

    tree = make_tree([
        make_heading("Parent", 1),
        make_paragraph("Parent content."),
        make_heading("Child", 2),
        child_table,
    ])

    candidates = HierarchyChunker().chunk(tree)

    assert len(candidates) == 2

    parent = candidates[0]
    child = candidates[1]

    assert parent.section_path == ["Parent"]
    assert "Parent content." in parent.text
    assert child_table not in parent.elements

    assert child.section_path == ["Parent", "Child"]
    assert child.text == "Section: Parent > Child"
    assert child.elements == [child_table]


def test_child_only_code_creates_child_candidate_for_delegation():

    child_code = make_code("print('child')")

    tree = make_tree([
        make_heading("Parent", 1),
        make_paragraph("Parent content."),
        make_heading("Child", 2),
        child_code,
    ])

    candidates = HierarchyChunker().chunk(tree)

    assert len(candidates) == 2

    parent = candidates[0]
    child = candidates[1]

    assert parent.section_path == ["Parent"]
    assert "Parent content." in parent.text
    assert child_code not in parent.elements

    assert child.section_path == ["Parent", "Child"]
    assert child.text == "Section: Parent > Child"
    assert child.elements == [child_code]


def test_child_table_does_not_leak_into_parent_candidate():

    tree = make_tree([
        make_heading("Parent", 1),

        make_paragraph("Parent content."),

        make_heading("Child", 2),

        make_table("Child table"),

        make_paragraph("Child narrative."),
    ])

    candidates = HierarchyChunker().chunk(tree)

    assert len(candidates) == 2

    parent = candidates[0]
    child = candidates[1]

    assert parent.text == (
        "Section: Parent\n\n"
        "Parent content."
    )

    assert "Child table" not in parent.text
    assert "Child narrative." not in parent.text

    assert child.text == (
        "Section: Parent > Child\n\n"
        "Child narrative."
    )


# ============================================================
# Whitespace handling
# ============================================================

def test_whitespace_only_elements_do_not_add_text():

    tree = make_tree([
        make_heading("Section", 1),

        make_paragraph("   "),

        make_paragraph("Real content."),

        make_paragraph("\n\t"),
    ])

    candidates = HierarchyChunker().chunk(tree)

    assert len(candidates) == 1

    assert candidates[0].text == (
        "Section: Section\n\n"
        "Real content."
    )


def test_whitespace_only_section_produces_no_candidate():

    tree = make_tree([
        make_heading("Section", 1),

        make_paragraph("   "),

        make_paragraph("\n\t"),
    ])

    candidates = HierarchyChunker().chunk(tree)

    assert candidates == []


def test_root_whitespace_is_ignored():

    tree = make_tree([
        make_paragraph("   "),
        make_paragraph("Real content."),
        make_paragraph("\n\t"),
    ])

    candidates = HierarchyChunker().chunk(tree)

    assert len(candidates) == 1

    assert candidates[0].text == (
        "Real content."
    )


# ============================================================
# Heading edge cases
# ============================================================

def test_heading_without_level_defaults_to_level_one():

    element = make_element(
        element_type=ElementType.HEADING,
        text="Introduction",
        metadata={},
    )

    tree = make_tree([
        element,
        make_paragraph("Introduction content."),
    ])

    candidates = HierarchyChunker().chunk(tree)

    assert len(candidates) == 1

    assert candidates[0].section_path == [
        "Introduction"
    ]

    assert "Introduction content." in candidates[0].text


def test_empty_heading_text():

    tree = make_tree([
        make_heading("", 1),
        make_paragraph("Some content."),
    ])

    candidates = HierarchyChunker().chunk(tree)

    assert len(candidates) == 1

    assert candidates[0].text == (
        "Some content."
    )


def test_whitespace_only_heading():

    tree = make_tree([
        make_heading("   ", 1),
        make_paragraph("Some content."),
    ])

    candidates = HierarchyChunker().chunk(tree)

    assert len(candidates) == 1

    assert candidates[0].text == (
        "Some content."
    )


# ============================================================
# Repeated heading names
# ============================================================

def test_repeated_heading_names_keep_distinct_paths():

    tree = make_tree([
        make_heading("Architecture", 1),

        make_heading("Overview", 2),
        make_paragraph("First overview."),

        make_heading("Architecture", 2),
        make_paragraph("Nested architecture."),
    ])

    candidates = HierarchyChunker().chunk(tree)

    assert len(candidates) == 2

    assert candidates[0].section_path == [
        "Architecture",
        "Overview",
    ]

    assert candidates[1].section_path == [
        "Architecture",
        "Architecture",
    ]


# ============================================================
# Complex document
# ============================================================

def test_complex_document_produces_expected_candidates():

    tree = make_tree([
        make_paragraph("Preamble."),

        make_heading("Introduction", 1),
        make_paragraph("Intro text."),

        make_heading("Architecture", 2),
        make_paragraph("Architecture text."),
        make_table("Architecture table"),

        make_heading("Implementation", 2),
        make_paragraph("Implementation text."),
        make_code("deploy()"),

        make_heading("Conclusion", 1),
        make_paragraph("Conclusion text."),
    ])

    candidates = HierarchyChunker().chunk(tree)

    assert len(candidates) == 5

    assert candidates[0].section_path == []
    assert candidates[0].text == "Preamble."

    assert candidates[1].section_path == [
        "Introduction"
    ]

    assert "Intro text." in candidates[1].text

    assert candidates[2].section_path == [
        "Introduction",
        "Architecture",
    ]

    assert "Architecture text." in candidates[2].text
    assert "Architecture table" not in candidates[2].text

    assert candidates[3].section_path == [
        "Introduction",
        "Implementation",
    ]

    assert "Implementation text." in candidates[3].text
    assert "deploy()" not in candidates[3].text

    assert candidates[4].section_path == [
        "Conclusion"
    ]

    assert candidates[4].text == (
        "Section: Conclusion\n\n"
        "Conclusion text."
    )