from pathlib import Path
from textwrap import dedent

import pytest

from app.enums.element_type import ElementType
from app.services.extraction.markdown_extractor import MarkdownExtractor


# ============================================================
# HELPERS
# ============================================================

def write_md(
    tmp_path: Path,
    content: str,
    filename: str = "test.md",
) -> Path:
    """
    Create a temporary Markdown file for the test.

    dedent() removes indentation introduced by Python's
    triple-quoted test strings so that the Markdown syntax
    itself is not accidentally changed.
    """
    file_path = tmp_path / filename

    content = dedent(content).strip()

    file_path.write_text(
        content,
        encoding="utf-8",
    )

    return file_path


def extract(
    tmp_path: Path,
    content: str,
    document_id: str = "test-doc",
    filename: str = "test.md",
):
    """
    Create Markdown file and run the extractor.
    """
    file_path = write_md(
        tmp_path,
        content,
        filename,
    )

    extractor = MarkdownExtractor()

    return extractor.extract(
        file_path=file_path,
        document_id=document_id,
        filename=filename,
    )


def elements_of_type(result, element_type):
    """
    Return only elements matching a particular ElementType.
    """
    return [
        element
        for element in result.elements
        if element.element_type == element_type
    ]


# ============================================================
# 1. EMPTY / BASIC DOCUMENT TESTS
# ============================================================

def test_empty_markdown(tmp_path):
    """
    Empty Markdown file should produce zero elements.
    """
    result = extract(tmp_path, "")

    assert result.elements == []


def test_whitespace_only_markdown(tmp_path):
    """
    Markdown containing only whitespace should produce zero elements.
    """
    result = extract(
        tmp_path,
        """
        
        
        """,
    )

    assert result.elements == []


def test_single_paragraph(tmp_path):
    """
    Basic paragraph extraction.
    """
    result = extract(
        tmp_path,
        "This is a simple paragraph.",
    )

    assert len(result.elements) == 1

    element = result.elements[0]

    assert element.element_type == ElementType.PARAGRAPH
    assert element.text == "This is a simple paragraph."


def test_multiple_paragraphs(tmp_path):
    """
    Multiple paragraphs should remain separate elements.
    """
    result = extract(
        tmp_path,
        """
        First paragraph.

        Second paragraph.

        Third paragraph.
        """,
    )

    paragraphs = elements_of_type(
        result,
        ElementType.PARAGRAPH,
    )

    assert len(paragraphs) == 3

    assert paragraphs[0].text == "First paragraph."
    assert paragraphs[1].text == "Second paragraph."
    assert paragraphs[2].text == "Third paragraph."


# ============================================================
# 2. HEADING TESTS
# ============================================================

@pytest.mark.parametrize(
    "markdown, expected_level, expected_text",
    [
        ("# Heading 1", 1, "Heading 1"),
        ("## Heading 2", 2, "Heading 2"),
        ("### Heading 3", 3, "Heading 3"),
        ("#### Heading 4", 4, "Heading 4"),
        ("##### Heading 5", 5, "Heading 5"),
        ("###### Heading 6", 6, "Heading 6"),
    ],
)
def test_heading_levels(
    tmp_path,
    markdown,
    expected_level,
    expected_text,
):
    """
    All Markdown heading levels should be detected correctly.
    """
    result = extract(
        tmp_path,
        markdown,
    )

    assert len(result.elements) == 1

    element = result.elements[0]

    assert element.element_type == ElementType.HEADING
    assert element.text == expected_text
    assert element.metadata["level"] == expected_level


def test_multiple_headings(tmp_path):
    """
    Multiple headings should preserve order.
    """
    result = extract(
        tmp_path,
        """
        # Chapter 1

        ## Section 1.1

        ### Section 1.1.1

        ## Section 1.2
        """,
    )

    headings = elements_of_type(
        result,
        ElementType.HEADING,
    )

    assert len(headings) == 4

    assert headings[0].text == "Chapter 1"
    assert headings[0].metadata["level"] == 1

    assert headings[1].text == "Section 1.1"
    assert headings[1].metadata["level"] == 2

    assert headings[2].text == "Section 1.1.1"
    assert headings[2].metadata["level"] == 3

    assert headings[3].text == "Section 1.2"
    assert headings[3].metadata["level"] == 2


def test_heading_with_inline_markdown(tmp_path):
    """
    Inline Markdown inside headings should not cause extraction failure.
    """
    result = extract(
        tmp_path,
        "# Hello **World**",
    )

    element = result.elements[0]

    assert element.element_type == ElementType.HEADING
    assert "Hello" in element.text
    assert "World" in element.text


def test_atx_heading_with_trailing_hashes(tmp_path):
    """
    Closing # characters should not become part of heading text.
    """
    result = extract(
        tmp_path,
        "# Heading ###",
    )

    element = result.elements[0]

    assert element.element_type == ElementType.HEADING
    assert element.text == "Heading"


# ============================================================
# 3. PARAGRAPH / INLINE MARKDOWN TESTS
# ============================================================

def test_paragraph_with_bold(tmp_path):
    """
    Bold Markdown should not cause extraction failure.
    """
    result = extract(
        tmp_path,
        "This is **bold** text.",
    )

    element = result.elements[0]

    assert element.element_type == ElementType.PARAGRAPH
    assert "bold" in element.text


def test_paragraph_with_italic(tmp_path):
    """
    Italic Markdown.
    """
    result = extract(
        tmp_path,
        "This is *italic* text.",
    )

    element = result.elements[0]

    assert element.element_type == ElementType.PARAGRAPH
    assert "italic" in element.text


def test_paragraph_with_inline_code(tmp_path):
    """
    Inline code should remain in paragraph content.
    """
    result = extract(
        tmp_path,
        "Use `python main.py` to run the application.",
    )

    element = result.elements[0]

    assert element.element_type == ElementType.PARAGRAPH
    assert "python main.py" in element.text


def test_paragraph_with_link(tmp_path):
    """
    Markdown links should not cause extraction failure.
    """
    result = extract(
        tmp_path,
        "Visit [OpenAI](https://openai.com).",
    )

    element = result.elements[0]

    assert element.element_type == ElementType.PARAGRAPH
    assert "OpenAI" in element.text


def test_paragraph_with_special_characters(tmp_path):
    """
    Special characters should survive extraction.
    """
    content = (
        "Special characters: "
        "! @ # $ % ^ & * ( ) - _ + = "
        "[ ] { } < > ? / \\ |"
    )

    result = extract(
        tmp_path,
        content,
    )

    assert result.elements[0].text == content


def test_unicode_text(tmp_path):
    """
    Unicode / multilingual text.
    """
    content = (
        "Hello नमस्ते — café — 日本語 — 中文 — 한국어 — 🚀"
    )

    result = extract(
        tmp_path,
        content,
    )

    assert result.elements[0].text == content


# ============================================================
# 4. ORDER INDEX TESTS
# ============================================================

def test_order_index_is_sequential(tmp_path):
    """
    Every extracted element should have sequential order indexes.
    """
    result = extract(
        tmp_path,
        """
        # Heading

        Paragraph.

        - Item 1
        - Item 2

        > Quote

        ```python
        print("hello")
        ```

        | A | B |
        |---|---|
        | 1 | 2 |
        """,
    )

    order_indexes = [
        element.order_index
        for element in result.elements
    ]

    assert order_indexes == list(
        range(len(result.elements))
    )


# ============================================================
# 5. ORDERED LIST TESTS
# ============================================================

def test_ordered_list(tmp_path):
    """
    Basic ordered list.
    """
    result = extract(
        tmp_path,
        """
        1. First
        2. Second
        3. Third
        """,
    )

    lists = elements_of_type(
        result,
        ElementType.LIST,
    )

    assert len(lists) == 3

    assert lists[0].text == "First"
    assert lists[1].text == "Second"
    assert lists[2].text == "Third"

    assert all(
        element.metadata["ordered"] is True
        for element in lists
    )


def test_ordered_list_with_non_one_start(tmp_path):
    """
    Markdown allows ordered lists beginning with numbers other than 1.
    """
    result = extract(
        tmp_path,
        """
        5. Five
        6. Six
        7. Seven
        """,
    )

    lists = elements_of_type(
        result,
        ElementType.LIST,
    )

    assert len(lists) == 3

    assert [item.text for item in lists] == [
        "Five",
        "Six",
        "Seven",
    ]

    assert all(
        item.metadata["ordered"] is True
        for item in lists
    )


def test_ordered_list_metadata(tmp_path):
    """
    Ordered list should contain expected metadata.
    """
    result = extract(
        tmp_path,
        "1. First",
        document_id="doc-123",
        filename="example.md",
    )

    element = result.elements[0]

    assert element.metadata["source"] == "markdown"
    assert element.metadata["document_id"] == "doc-123"
    assert element.metadata["filename"] == "example.md"
    assert element.metadata["ordered"] is True
    assert element.metadata["indent_level"] == 0


# ============================================================
# 6. BULLET LIST TESTS
# ============================================================

@pytest.mark.parametrize(
    "marker",
    ["-", "*", "+"],
)
def test_bullet_list_markers(
    tmp_path,
    marker,
):
    """
    -, * and + should all be recognized as unordered lists.
    """
    result = extract(
        tmp_path,
        f"""
        {marker} First
        {marker} Second
        {marker} Third
        """,
    )

    lists = elements_of_type(
        result,
        ElementType.LIST,
    )

    assert len(lists) == 3

    assert [item.text for item in lists] == [
        "First",
        "Second",
        "Third",
    ]

    assert all(
        item.metadata["ordered"] is False
        for item in lists
    )


# ============================================================
# 7. NESTED LIST TESTS
# ============================================================

def test_nested_bullet_list(tmp_path):
    """
    Nested unordered lists should preserve nesting depth.
    """
    result = extract(
        tmp_path,
        """
        - Parent
          - Child
            - Grandchild
        """,
    )

    lists = elements_of_type(
        result,
        ElementType.LIST,
    )

    assert len(lists) == 3

    assert lists[0].text == "Parent"
    assert lists[1].text == "Child"
    assert lists[2].text == "Grandchild"

    assert lists[0].metadata["indent_level"] == 0
    assert lists[1].metadata["indent_level"] == 1
    assert lists[2].metadata["indent_level"] == 2


def test_nested_ordered_list(tmp_path):
    """
    Nested ordered lists.
    """
    result = extract(
        tmp_path,
        """
        1. Parent
           1. Child
              1. Grandchild
        """,
    )

    lists = elements_of_type(
        result,
        ElementType.LIST,
    )

    assert len(lists) == 3

    assert all(
        item.metadata["ordered"] is True
        for item in lists
    )

    assert lists[0].metadata["indent_level"] == 0
    assert lists[1].metadata["indent_level"] == 1
    assert lists[2].metadata["indent_level"] == 2


def test_mixed_nested_lists(tmp_path):
    """
    Ordered list containing unordered list and vice versa.
    """
    result = extract(
        tmp_path,
        """
        1. Parent
           - Child A
           - Child B
        2. Parent 2
           - Child C
        """,
    )

    lists = elements_of_type(
        result,
        ElementType.LIST,
    )

    assert len(lists) == 5

    assert lists[0].text == "Parent"
    assert lists[0].metadata["ordered"] is True
    assert lists[0].metadata["indent_level"] == 0

    assert lists[1].text == "Child A"
    assert lists[1].metadata["ordered"] is False
    assert lists[1].metadata["indent_level"] == 1

    assert lists[2].text == "Child B"
    assert lists[2].metadata["ordered"] is False
    assert lists[2].metadata["indent_level"] == 1


def test_list_with_multiple_paragraphs(tmp_path):
    """
    List item containing continuation content.
    """
    result = extract(
        tmp_path,
        """
        - First item

          continuation of first item

        - Second item
        """,
    )

    lists = elements_of_type(
        result,
        ElementType.LIST,
    )

    assert len(lists) >= 2


# ============================================================
# 8. BLOCKQUOTE TESTS
# ============================================================

def test_basic_blockquote(tmp_path):
    """
    Basic blockquote extraction.
    """
    result = extract(
        tmp_path,
        "> This is a quote.",
    )

    quotes = elements_of_type(
        result,
        ElementType.QUOTE,
    )

    assert len(quotes) == 1
    assert quotes[0].text == "This is a quote."


def test_multiline_blockquote(tmp_path):
    """
    Multiple quote lines should be preserved.
    """
    result = extract(
        tmp_path,
        """
        > First line
        > Second line
        > Third line
        """,
    )

    quotes = elements_of_type(
        result,
        ElementType.QUOTE,
    )

    assert len(quotes) == 1

    assert quotes[0].text == (
        "First line\n"
        "Second line\n"
        "Third line"
    )


def test_nested_blockquote(tmp_path):
    """
    Nested blockquotes should not crash.
    """
    result = extract(
        tmp_path,
        """
        > Outer quote
        >
        >> Inner quote
        """,
    )

    quotes = elements_of_type(
        result,
        ElementType.QUOTE,
    )

    assert len(quotes) >= 1
    assert "Outer quote" in quotes[0].text


# ============================================================
# 9. CODE BLOCK TESTS
# ============================================================

def test_fenced_code_block(tmp_path):
    """
    Basic fenced code block.
    """
    result = extract(
        tmp_path,
        """
        ```python
        print("Hello")
        ```
        """,
    )

    code_blocks = elements_of_type(
        result,
        ElementType.CODE_BLOCK,
    )

    assert len(code_blocks) == 1

    code = code_blocks[0]

    assert code.text == 'print("Hello")\n'
    assert code.metadata["language"] == "python"


@pytest.mark.parametrize(
    "language",
    [
        "python",
        "java",
        "javascript",
        "typescript",
        "json",
        "sql",
        "bash",
        "html",
        "css",
        "yaml",
        "xml",
    ],
)
def test_code_block_languages(
    tmp_path,
    language,
):
    """
    Language identifier should be captured.
    """
    result = extract(
        tmp_path,
        f"""
        ```{language}
        example code
        ```
        """,
    )

    code_blocks = elements_of_type(
        result,
        ElementType.CODE_BLOCK,
    )

    assert len(code_blocks) == 1

    assert code_blocks[0].metadata["language"] == language


def test_code_block_without_language(tmp_path):
    """
    Fenced code without language should produce None language.
    """
    result = extract(
        tmp_path,
        """
        ```
        some code
        ```
        """,
    )

    code_blocks = elements_of_type(
        result,
        ElementType.CODE_BLOCK,
    )

    assert len(code_blocks) == 1

    assert code_blocks[0].metadata["language"] is None


def test_empty_code_block(tmp_path):
    """
    Empty fenced code block.
    """
    result = extract(
        tmp_path,
        """
        ```
        ```
        """,
    )

    code_blocks = elements_of_type(
        result,
        ElementType.CODE_BLOCK,
    )

    assert len(code_blocks) == 1
    assert code_blocks[0].text == ""


def test_code_with_backticks_inside(tmp_path):
    """
    Code containing backticks should not be accidentally truncated
    when using a longer fence.
    """
    result = extract(
        tmp_path,
        """
        ````python
        value = `hello`
        print(value)
        ````
        """,
    )

    code_blocks = elements_of_type(
        result,
        ElementType.CODE_BLOCK,
    )

    assert len(code_blocks) == 1

    assert "`hello`" in code_blocks[0].text


def test_multiple_code_blocks(tmp_path):
    """
    Multiple independent code blocks.
    """
    result = extract(
        tmp_path,
        """
        ```python
        print("Python")
        ```

        ```java
        System.out.println("Java");
        ```
        """,
    )

    code_blocks = elements_of_type(
        result,
        ElementType.CODE_BLOCK,
    )

    assert len(code_blocks) == 2

    assert code_blocks[0].metadata["language"] == "python"
    assert code_blocks[1].metadata["language"] == "java"


def test_code_indentation_preserved(tmp_path):
    """
    Code indentation must not be destroyed.
    """
    result = extract(
        tmp_path,
        """
        ```python
        def hello():
            if True:
                print("Hello")
        ```
        """,
    )

    code_blocks = elements_of_type(
        result,
        ElementType.CODE_BLOCK,
    )

    assert len(code_blocks) == 1

    code = code_blocks[0]

    assert "    if True:" in code.text
    assert '        print("Hello")' in code.text


# ============================================================
# 10. TABLE TESTS
# ============================================================

def test_basic_table(tmp_path):
    """
    Basic Markdown table.
    """
    result = extract(
        tmp_path,
        """
        | Name | Age |
        |------|-----|
        | Abhishek | 20 |
        | Rahul | 21 |
        """,
    )

    tables = elements_of_type(
        result,
        ElementType.TABLE,
    )

    assert len(tables) == 1

    table = tables[0]

    assert table.metadata["n_rows"] == 3
    assert table.metadata["n_cols"] == 2

    assert table.metadata["cells"] == [
        ["Name", "Age"],
        ["Abhishek", "20"],
        ["Rahul", "21"],
    ]


def test_table_header_detection(tmp_path):
    """
    Normal textual header should be detected.
    """
    result = extract(
        tmp_path,
        """
        | Name | Age | City |
        |------|-----|------|
        | Abhishek | 20 | Mumbai |
        | Rahul | 21 | Pune |
        """,
    )

    tables = elements_of_type(
        result,
        ElementType.TABLE,
    )

    assert len(tables) == 1

    table = tables[0]

    assert table.metadata["has_header_row"] is True


def test_numeric_first_row_table(tmp_path):
    """
    Numeric first row should normally not be treated as a header.
    """
    result = extract(
        tmp_path,
        """
        | 10 | 20 | 30 |
        |----|----|----|
        | 40 | 50 | 60 |
        | 70 | 80 | 90 |
        """,
    )

    tables = elements_of_type(
        result,
        ElementType.TABLE,
    )

    assert len(tables) == 1

    table = tables[0]

    assert table.metadata["has_header_row"] is False


def test_table_without_header_semantically(tmp_path):
    """
    A table whose first row contains actual data should be tested
    against the extractor's header heuristic.
    """
    result = extract(
        tmp_path,
        """
        | Apple | 10 | Red |
        |-------|----|-----|
        | Banana | 20 | Yellow |
        | Mango | 15 | Green |
        """,
    )

    tables = elements_of_type(
        result,
        ElementType.TABLE,
    )

    assert len(tables) == 1

    table = tables[0]

    assert table.metadata["cells"][0] == [
        "Apple",
        "10",
        "Red",
    ]


def test_table_markdown_generation(tmp_path):
    """
    Generated Markdown table should contain the header separator
    exactly once.
    """
    result = extract(
        tmp_path,
        """
        | Name | Age |
        |------|-----|
        | A | 10 |
        | B | 20 |
        """,
    )

    table = elements_of_type(
        result,
        ElementType.TABLE,
    )[0]

    markdown = table.metadata["markdown"]

    assert "| Name | Age |" in markdown
    assert "| A | 10 |" in markdown
    assert "| B | 20 |" in markdown


def test_table_header_not_duplicated(tmp_path):
    """
    Regression test for duplicated first-row issue.
    """
    result = extract(
        tmp_path,
        """
        | Name | Age |
        |------|-----|
        | Abhishek | 20 |
        | Rahul | 21 |
        """,
    )

    table = elements_of_type(
        result,
        ElementType.TABLE,
    )[0]

    markdown = table.metadata["markdown"]

    assert markdown.count("| Name | Age |") == 1


def test_multiple_tables(tmp_path):
    """
    Multiple tables must receive unique sequential table IDs.
    """
    result = extract(
        tmp_path,
        """
        | A | B |
        |---|---|
        | 1 | 2 |

        Some paragraph.

        | C | D |
        |---|---|
        | 3 | 4 |

        Another paragraph.

        | E | F |
        |---|---|
        | 5 | 6 |
        """,
        document_id="multi-table-doc",
    )

    tables = elements_of_type(
        result,
        ElementType.TABLE,
    )

    assert len(tables) == 3

    assert tables[0].metadata["table_index"] == 0
    assert tables[1].metadata["table_index"] == 1
    assert tables[2].metadata["table_index"] == 2

    assert tables[0].metadata["table_id"] == (
        "multi-table-doc-table-0"
    )

    assert tables[1].metadata["table_id"] == (
        "multi-table-doc-table-1"
    )

    assert tables[2].metadata["table_id"] == (
        "multi-table-doc-table-2"
    )


def test_table_without_document_id(tmp_path):
    """
    Table ID should still be generated when document_id is absent.
    """
    result = extract(
        tmp_path,
        """
        | A | B |
        |---|---|
        | 1 | 2 |
        """,
        document_id=None,
    )

    table = elements_of_type(
        result,
        ElementType.TABLE,
    )[0]

    assert table.metadata["table_id"] == "table-0"


def test_table_empty_cells(tmp_path):
    """
    Empty cells should not crash extraction.
    """
    result = extract(
        tmp_path,
        """
        | Name | Age | City |
        |------|-----|------|
        | Abhishek | | Mumbai |
        | | 21 | Pune |
        """,
    )

    tables = elements_of_type(
        result,
        ElementType.TABLE,
    )

    assert len(tables) == 1

    table = tables[0]

    assert table.metadata["cells"][1] == [
        "Abhishek",
        "",
        "Mumbai",
    ]

    assert table.metadata["cells"][2] == [
        "",
        "21",
        "Pune",
    ]


def test_table_single_column(tmp_path):
    """
    Single-column table.
    """
    result = extract(
        tmp_path,
        """
        | Name |
        |------|
        | Abhishek |
        | Rahul |
        """,
    )

    table = elements_of_type(
        result,
        ElementType.TABLE,
    )[0]

    assert table.metadata["n_cols"] == 1
    assert table.metadata["n_rows"] == 3


def test_table_many_columns(tmp_path):
    """
    Wide table.
    """
    result = extract(
        tmp_path,
        """
        | A | B | C | D | E | F | G | H |
        |---|---|---|---|---|---|---|---|
        | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 |
        """,
    )

    table = elements_of_type(
        result,
        ElementType.TABLE,
    )[0]

    assert table.metadata["n_cols"] == 8


def test_table_with_inline_markdown(tmp_path):
    """
    Inline Markdown inside table cells.
    """
    result = extract(
        tmp_path,
        """
        | Name | Description |
        |------|-------------|
        | **Abhishek** | *Developer* |
        """,
    )

    table = elements_of_type(
        result,
        ElementType.TABLE,
    )[0]

    assert "Abhishek" in table.metadata["cells"][1][0]
    assert "Developer" in table.metadata["cells"][1][1]


# ============================================================
# 11. TABLE ALIGNMENT TESTS
# ============================================================

@pytest.mark.parametrize(
    "separator",
    [
        ":---",
        "---:",
        ":---:",
    ],
)
def test_table_alignment(
    tmp_path,
    separator,
):
    """
    Left/right/center aligned Markdown tables.
    """
    result = extract(
        tmp_path,
        f"""
        | Name |
        |{separator}|
        | Abhishek |
        """,
    )

    tables = elements_of_type(
        result,
        ElementType.TABLE,
    )

    assert len(tables) == 1


# ============================================================
# 12. SPECIAL TABLE CONTENT
# ============================================================

def test_table_with_pipe_inside_code(tmp_path):
    """
    Escaped pipe inside table cell.
    """
    result = extract(
        tmp_path,
        r"""
        | Command | Description |
        |---------|-------------|
        | `a \| b` | Pipe operation |
        """,
    )

    tables = elements_of_type(
        result,
        ElementType.TABLE,
    )

    assert len(tables) == 1


def test_table_with_urls(tmp_path):
    """
    URLs inside tables.
    """
    result = extract(
        tmp_path,
        """
        | Name | URL |
        |------|-----|
        | OpenAI | https://openai.com |
        """,
    )

    table = elements_of_type(
        result,
        ElementType.TABLE,
    )[0]

    assert "https://openai.com" in (
        table.metadata["cells"][1][1]
    )


# ============================================================
# 13. DOCUMENT METADATA TESTS
# ============================================================

def test_document_metadata(tmp_path):
    """
    Every element should contain common metadata.
    """
    result = extract(
        tmp_path,
        """
        # Heading

        Paragraph.

        - List

        > Quote

        ```python
        print("hello")
        ```

        | A | B |
        |---|---|
        | 1 | 2 |
        """,
        document_id="doc-123",
        filename="sample.md",
    )

    for element in result.elements:
        assert element.metadata["document_id"] == "doc-123"
        assert element.metadata["filename"] == "sample.md"
        assert element.metadata["source"] == "markdown"


# ============================================================
# 14. MIXED DOCUMENT TEST
# ============================================================

def test_complete_mixed_markdown_document(tmp_path):
    """
    Full Markdown document containing every supported element type.
    """
    markdown = """
    # Intellex

    This is an introduction paragraph.

    ## Features

    1. Document ingestion
    2. Chunking
    3. Retrieval

    - Python
    - FastAPI
    - PostgreSQL
      - pgvector
      - SQLAlchemy

    > This is an important architectural note.

    ### Example Code

    ```python
    def hello():
        print("Hello Intellex")
    ```

    ### Comparison

    | Component | Technology |
    |-----------|------------|
    | Backend | FastAPI |
    | Database | PostgreSQL |
    | Vector Store | pgvector |

    Final paragraph.
    """

    result = extract(
        tmp_path,
        markdown,
        document_id="intellex",
        filename="intellex.md",
    )

    assert len(result.elements) > 0

    headings = elements_of_type(
        result,
        ElementType.HEADING,
    )

    paragraphs = elements_of_type(
        result,
        ElementType.PARAGRAPH,
    )

    lists = elements_of_type(
        result,
        ElementType.LIST,
    )

    quotes = elements_of_type(
        result,
        ElementType.QUOTE,
    )

    code_blocks = elements_of_type(
        result,
        ElementType.CODE_BLOCK,
    )

    tables = elements_of_type(
        result,
        ElementType.TABLE,
    )

    assert len(headings) == 4
    assert len(paragraphs) == 2
    assert len(lists) == 8
    assert len(quotes) == 1
    assert len(code_blocks) == 1
    assert len(tables) == 1


# ============================================================
# 15. STATE / REUSABILITY TESTS
# ============================================================

def test_same_extractor_multiple_files(tmp_path):
    """
    Reusing the same extractor instance must reset table indexes.
    """
    extractor = MarkdownExtractor()

    file1 = write_md(
        tmp_path,
        """
        | A | B |
        |---|---|
        | 1 | 2 |
        """,
        "file1.md",
    )

    file2 = write_md(
        tmp_path,
        """
        | C | D |
        |---|---|
        | 3 | 4 |
        """,
        "file2.md",
    )

    result1 = extractor.extract(
        file1,
        document_id="doc-1",
        filename="file1.md",
    )

    result2 = extractor.extract(
        file2,
        document_id="doc-2",
        filename="file2.md",
    )

    table1 = elements_of_type(
        result1,
        ElementType.TABLE,
    )[0]

    table2 = elements_of_type(
        result2,
        ElementType.TABLE,
    )[0]

    assert table1.metadata["table_index"] == 0
    assert table2.metadata["table_index"] == 0

    assert table1.metadata["table_id"] == "doc-1-table-0"
    assert table2.metadata["table_id"] == "doc-2-table-0"


# ============================================================
# 16. FILE INPUT TESTS
# ============================================================

def test_path_object_input(tmp_path):
    """
    Extractor should accept pathlib.Path.
    """
    file_path = write_md(
        tmp_path,
        "# Hello",
    )

    extractor = MarkdownExtractor()

    result = extractor.extract(
        file_path,
        document_id="path-test",
        filename="test.md",
    )

    assert len(result.elements) == 1
    assert result.elements[0].text == "Hello"


def test_string_path_input(tmp_path):
    """
    Extractor should also accept string path.
    """
    file_path = write_md(
        tmp_path,
        "# Hello",
    )

    extractor = MarkdownExtractor()

    result = extractor.extract(
        str(file_path),
        document_id="string-path-test",
        filename="test.md",
    )

    assert len(result.elements) == 1
    assert result.elements[0].text == "Hello"


def test_missing_file(tmp_path):
    """
    Missing Markdown file should raise FileNotFoundError.
    """
    extractor = MarkdownExtractor()

    missing_file = tmp_path / "does_not_exist.md"

    with pytest.raises(FileNotFoundError):
        extractor.extract(
            missing_file,
            document_id="missing",
            filename="missing.md",
        )


# ============================================================
# 17. ENCODING TESTS
# ============================================================

def test_utf8_markdown(tmp_path):
    """
    UTF-8 Markdown should be read correctly.
    """
    content = """
    # नमस्ते

    यह एक परीक्षण है।

    | नाम | शहर |
    |-----|-----|
    | अभिषेक | मुंबई |
    """

    result = extract(
        tmp_path,
        content,
    )

    assert result.elements[0].text == "नमस्ते"

    table = elements_of_type(
        result,
        ElementType.TABLE,
    )[0]

    assert table.metadata["cells"][1][0] == "अभिषेक"


# ============================================================
# 18. LONG CONTENT TEST
# ============================================================

def test_large_markdown_document(tmp_path):
    """
    Large Markdown document should not crash or lose major structure.
    """
    sections = []

    for i in range(100):
        sections.append(
            f"""
            ## Section {i}

            This is paragraph {i}.

            - Item A
            - Item B
            - Item C
            """
        )

    content = "\n".join(sections)

    result = extract(
        tmp_path,
        content,
    )

    headings = elements_of_type(
        result,
        ElementType.HEADING,
    )

    paragraphs = elements_of_type(
        result,
        ElementType.PARAGRAPH,
    )

    lists = elements_of_type(
        result,
        ElementType.LIST,
    )

    assert len(headings) == 100
    assert len(paragraphs) == 100
    assert len(lists) == 300


# ============================================================
# 19. REGRESSION TESTS
# ============================================================

def test_table_index_regression(tmp_path):
    """
    Regression:
    Multiple tables must not reuse the same table index.
    """
    content = """
    | A | B |
    |---|---|
    | 1 | 2 |

    | C | D |
    |---|---|
    | 3 | 4 |

    | E | F |
    |---|---|
    | 5 | 6 |
    """

    result = extract(
        tmp_path,
        content,
        document_id="regression",
    )

    tables = elements_of_type(
        result,
        ElementType.TABLE,
    )

    indexes = [
        table.metadata["table_index"]
        for table in tables
    ]

    assert indexes == [0, 1, 2]


def test_table_id_regression(tmp_path):
    """
    Regression:
    Table IDs must remain unique.
    """
    result = extract(
        tmp_path,
        """
        | A | B |
        |---|---|
        | 1 | 2 |

        | C | D |
        |---|---|
        | 3 | 4 |
        """,
        document_id="regression",
    )

    tables = elements_of_type(
        result,
        ElementType.TABLE,
    )

    ids = [
        table.metadata["table_id"]
        for table in tables
    ]

    assert ids == [
        "regression-table-0",
        "regression-table-1",
    ]

    assert len(ids) == len(set(ids))


def test_no_duplicate_table_header(tmp_path):
    """
    Regression:
    Header must not be duplicated in generated Markdown.
    """
    result = extract(
        tmp_path,
        """
        | Name | Age | City |
        |------|-----|------|
        | Abhishek | 20 | Mumbai |
        | Rahul | 21 | Pune |
        """,
    )

    table = elements_of_type(
        result,
        ElementType.TABLE,
    )[0]

    markdown = table.metadata["markdown"]

    assert markdown.count("| Name | Age | City |") == 1


# ============================================================
# 20. ELEMENT TYPE SANITY CHECK
# ============================================================

def test_only_supported_element_types_are_returned(tmp_path):
    """
    Extractor should only return supported element types.
    """
    result = extract(
        tmp_path,
        """
        # Heading

        Paragraph.

        - List

        > Quote

        ```python
        print("hello")
        ```

        | A | B |
        |---|---|
        | 1 | 2 |
        """,
    )

    supported_types = {
        ElementType.HEADING,
        ElementType.PARAGRAPH,
        ElementType.LIST,
        ElementType.QUOTE,
        ElementType.CODE_BLOCK,
        ElementType.TABLE,
    }

    for element in result.elements:
        assert element.element_type in supported_types


# ============================================================
# 21. SOURCE FILE IMMUTABILITY
# ============================================================

def test_source_file_not_modified(tmp_path):
    """
    Extraction must be read-only.
    """
    content = """
    # Test

    Some content.

    | A | B |
    |---|---|
    | 1 | 2 |
    """

    file_path = write_md(
        tmp_path,
        content,
    )

    before = file_path.read_text(
        encoding="utf-8",
    )

    extractor = MarkdownExtractor()

    extractor.extract(
        file_path,
        document_id="readonly",
        filename="test.md",
    )

    after = file_path.read_text(
        encoding="utf-8",
    )

    assert before == after