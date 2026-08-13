import pytest

from app.dto.code_chunk import CodeChunk
from app.dto.extracted_element import ExtractedElement
from app.dto.routed_chunk import RoutedChunk
from app.enums.chunk_type import ChunkType
from app.enums.element_type import ElementType
from app.services.chunking.code.code_chunker import CodeChunker


# =========================================================
# HELPERS
# =========================================================

def make_code_element(
    code: str,
    order_index: int = 0,
    language: str | None = "python",
    metadata: dict | None = None,
) -> ExtractedElement:

    element_metadata = metadata.copy() if metadata else {}

    if language is not None:
        element_metadata["language"] = language

    return ExtractedElement(
        order_index=order_index,
        text=code,
        element_type=ElementType.CODE_BLOCK,
        metadata=element_metadata,
    )


def make_routed_chunk(
    code: str,
    order_index: int = 0,
    language: str | None = "python",
    section_path: list[str] | None = None,
    metadata: dict | None = None,
) -> RoutedChunk:

    element = make_code_element(
        code=code,
        order_index=order_index,
        language=language,
        metadata=metadata,
    )

    return RoutedChunk(
        chunk_type=next(iter(ChunkType)),
        elements=[element],
        text=code,
        section_path=section_path or [],
        order_index=order_index,
    )


# =========================================================
# 1. BASIC INPUT VALIDATION
# =========================================================

def test_empty_elements_returns_empty():

    routed_chunk = RoutedChunk(
        chunk_type=next(iter(ChunkType)),
        elements=[],
        text=None,
        section_path=[],
        order_index=0,
    )

    chunker = CodeChunker()

    result = chunker.chunk(routed_chunk)

    assert result == []


def test_empty_code_returns_empty():

    routed_chunk = make_routed_chunk(
        code=""
    )

    chunker = CodeChunker()

    result = chunker.chunk(routed_chunk)

    assert result == []


def test_whitespace_only_code_returns_empty():

    routed_chunk = make_routed_chunk(
        code="   \n\t  "
    )

    chunker = CodeChunker()

    result = chunker.chunk(routed_chunk)

    assert result == []


def test_multiple_elements_uses_first_element():

    element_1 = make_code_element(
        code="first code",
        order_index=10,
    )

    element_2 = make_code_element(
        code="second code",
        order_index=20,
    )

    routed_chunk = RoutedChunk(
        chunk_type=next(iter(ChunkType)),
        elements=[
            element_1,
            element_2,
        ],
        text="first code",
        section_path=[],
        order_index=10,
    )

    chunker = CodeChunker()

    result = chunker.chunk(routed_chunk)

    assert len(result) == 1
    assert result[0].text == "first code"
    assert result[0].elements[0].order_index == 10


# =========================================================
# 2. SIZE BOUNDARY
# =========================================================

def test_code_exactly_at_limit_fits():

    chunker = CodeChunker(
        max_tokens=100
    )

    code = "a" * 400

    assert chunker._fits(code) is True

    routed_chunk = make_routed_chunk(
        code=code
    )

    result = chunker.chunk(routed_chunk)

    assert len(result) == 1
    assert result[0].text == code


def test_code_one_character_over_limit():

    chunker = CodeChunker(
        max_tokens=100
    )

    code = "a" * 401

    assert chunker._fits(code) is False


def test_tiny_max_tokens_does_not_crash():

    chunker = CodeChunker(
        max_tokens=1
    )

    code = (
        "def hello():\n"
        "    return 1\n"
    )

    routed_chunk = make_routed_chunk(
        code=code
    )

    result = chunker.chunk(routed_chunk)

    assert result

    assert all(
        isinstance(chunk, CodeChunk)
        for chunk in result
    )


def test_large_max_tokens_keeps_code_together():

    chunker = CodeChunker(
        max_tokens=1_000_000
    )

    code = (
        "def hello():\n"
        "    return 1\n"
    )

    routed_chunk = make_routed_chunk(
        code=code
    )

    result = chunker.chunk(routed_chunk)

    assert len(result) == 1
    assert result[0].text == code


# =========================================================
# 3. LANGUAGE HANDLING
# =========================================================

def test_missing_language_uses_line_fallback():

    code = "\n".join(
        f"line {i}"
        for i in range(50)
    )

    routed_chunk = make_routed_chunk(
        code=code,
        language=None,
    )

    chunker = CodeChunker(
        max_tokens=1
    )

    result = chunker.chunk(routed_chunk)

    assert len(result) > 1


def test_empty_metadata_uses_line_fallback():

    code = "\n".join(
        f"line {i}"
        for i in range(50)
    )

    element = ExtractedElement(
        order_index=0,
        text=code,
        element_type=ElementType.CODE_BLOCK,
        metadata={},
    )

    routed_chunk = RoutedChunk(
        chunk_type=next(iter(ChunkType)),
        elements=[element],
        text=code,
        section_path=[],
        order_index=0,
    )

    chunker = CodeChunker(
        max_tokens=1
    )

    result = chunker.chunk(routed_chunk)

    assert result


def test_unsupported_language_does_not_crash():

    code = "\n".join(
        f"line {i}"
        for i in range(50)
    )

    routed_chunk = make_routed_chunk(
        code=code,
        language="rust",
    )

    chunker = CodeChunker(
        max_tokens=1
    )

    result = chunker.chunk(routed_chunk)

    assert result


def test_uppercase_python_language_is_supported():

    code = (
        "class User:\n"
        "    pass\n"
        "\n"
        "class Admin:\n"
        "    pass\n"
    )

    chunker = CodeChunker(
        max_tokens=1
    )

    parts = chunker._split_structurally(
        code=code,
        language="PYTHON",
    )

    assert len(parts) >= 2
    assert "".join(parts) == code


def test_mixed_case_python_language_is_supported():

    code = (
        "class User:\n"
        "    pass\n"
        "\n"
        "class Admin:\n"
        "    pass\n"
    )

    chunker = CodeChunker(
        max_tokens=1
    )

    parts = chunker._split_structurally(
        code=code,
        language="PyThOn",
    )

    assert len(parts) >= 2
    assert "".join(parts) == code


# =========================================================
# 4. PYTHON STRUCTURAL SPLITTING
# =========================================================

def test_python_multiple_classes_split_structurally():

    code = (
        "class User:\n"
        "    pass\n"
        "\n"
        "class Admin:\n"
        "    pass\n"
    )

    chunker = CodeChunker(
        max_tokens=1
    )

    parts = chunker._split_structurally(
        code=code,
        language="python",
    )

    assert len(parts) == 2
    assert "".join(parts) == code


def test_python_multiple_functions_split_structurally():

    code = (
        "def first():\n"
        "    return 1\n"
        "\n"
        "def second():\n"
        "    return 2\n"
    )

    chunker = CodeChunker(
        max_tokens=1
    )

    parts = chunker._split_structurally(
        code=code,
        language="python",
    )

    assert len(parts) == 2
    assert "".join(parts) == code


def test_python_async_function_marker():

    code = (
        "async def fetch():\n"
        "    return 1\n"
        "\n"
        "async def save():\n"
        "    return 2\n"
    )

    chunker = CodeChunker(
        max_tokens=1
    )

    parts = chunker._split_structurally(
        code=code,
        language="python",
    )

    assert len(parts) == 2
    assert "".join(parts) == code


# =========================================================
# 5. PYTHON INDENTED METHODS
# =========================================================

def test_python_indented_methods_are_detected():

    code = (
        "class User:\n"
        "    def create(self):\n"
        "        return 1\n"
        "\n"
        "    def delete(self):\n"
        "        return 2\n"
    )

    chunker = CodeChunker(
        max_tokens=1
    )

    parts = chunker._split_structurally(
        code=code,
        language="python",
    )

    assert len(parts) == 3
    assert "".join(parts) == code

    assert parts[0] == (
        "class User:\n"
    )

    assert parts[1] == (
        "    def create(self):\n"
        "        return 1\n"
        "\n"
    )

    assert parts[2] == (
        "    def delete(self):\n"
        "        return 2\n"
    )


def test_python_nested_function_is_detected():

    code = (
        "def outer():\n"
        "    def inner():\n"
        "        return 1\n"
        "    return inner\n"
    )

    chunker = CodeChunker(
        max_tokens=1
    )

    parts = chunker._split_structurally(
        code=code,
        language="python",
    )

    assert len(parts) == 2
    assert "".join(parts) == code

    assert parts[0] == (
        "def outer():\n"
    )

    assert parts[1] == (
        "    def inner():\n"
        "        return 1\n"
        "    return inner\n"
    )


def test_python_class_with_methods_preserves_source():

    code = (
        "class User:\n"
        "\n"
        "    def create(self):\n"
        "        return True\n"
        "\n"
        "    def delete(self):\n"
        "        return True\n"
    )

    chunker = CodeChunker(
        max_tokens=1
    )

    parts = chunker._split_structurally(
        code=code,
        language="python",
    )

    assert "".join(parts) == code


# =========================================================
# 6. FALSE POSITIVE / LINE BOUNDARY
# =========================================================

def test_marker_must_start_at_line_boundary():

    code = (
        'message = "def fake():"\n'
        "def real():\n"
        "    return 1\n"
    )

    chunker = CodeChunker(
        max_tokens=1
    )

    parts = chunker._split_structurally(
        code=code,
        language="python",
    )

    assert len(parts) == 2
    assert "".join(parts) == code

    assert parts[0] == (
        'message = "def fake():"\n'
    )

    assert parts[1] == (
        "def real():\n"
        "    return 1\n"
    )


def test_text_containing_def_mid_line_is_not_marker():

    code = (
        'message = "please def something"\n'
        "def real():\n"
        "    return 1\n"
    )

    chunker = CodeChunker(
        max_tokens=1
    )

    parts = chunker._split_structurally(
        code=code,
        language="python",
    )

    assert len(parts) == 2
    assert "".join(parts) == code


# =========================================================
# 7. JAVASCRIPT
# =========================================================

def test_javascript_functions_split():

    code = (
        "function foo() {\n"
        "    return 1;\n"
        "}\n"
        "\n"
        "function bar() {\n"
        "    return 2;\n"
        "}\n"
    )

    chunker = CodeChunker(
        max_tokens=1
    )

    parts = chunker._split_structurally(
        code=code,
        language="javascript",
    )

    assert len(parts) == 2
    assert "".join(parts) == code


def test_javascript_classes_split():

    code = (
        "class User {\n"
        "}\n"
        "\n"
        "class Admin {\n"
        "}\n"
    )

    chunker = CodeChunker(
        max_tokens=1
    )

    parts = chunker._split_structurally(
        code=code,
        language="javascript",
    )

    assert len(parts) == 2
    assert "".join(parts) == code


# =========================================================
# 8. TYPESCRIPT
# =========================================================

def test_typescript_functions_split():

    code = (
        "function add(a: number, b: number) {\n"
        "    return a + b;\n"
        "}\n"
        "\n"
        "function subtract(a: number, b: number) {\n"
        "    return a - b;\n"
        "}\n"
    )

    chunker = CodeChunker(
        max_tokens=1
    )

    parts = chunker._split_structurally(
        code=code,
        language="typescript",
    )

    assert len(parts) == 2
    assert "".join(parts) == code


# =========================================================
# 9. JAVA
# =========================================================

def test_java_multiple_classes_split():

    code = (
        "class User {\n"
        "}\n"
        "\n"
        "class Admin {\n"
        "}\n"
    )

    chunker = CodeChunker(
        max_tokens=1
    )

    parts = chunker._split_structurally(
        code=code,
        language="java",
    )

    assert len(parts) == 2
    assert "".join(parts) == code


def test_java_indented_methods_are_detected():

    code = (
        "class User {\n"
        "    public void save() {\n"
        "        // save\n"
        "    }\n"
        "\n"
        "    private void delete() {\n"
        "        // delete\n"
        "    }\n"
        "}\n"
    )

    chunker = CodeChunker(
        max_tokens=1
    )

    parts = chunker._split_structurally(
        code=code,
        language="java",
    )

    assert len(parts) == 3
    assert "".join(parts) == code

    assert parts[0] == (
        "class User {\n"
    )

    assert parts[1] == (
        "    public void save() {\n"
        "        // save\n"
        "    }\n"
        "\n"
    )

    assert parts[2] == (
        "    private void delete() {\n"
        "        // delete\n"
        "    }\n"
        "}\n"
    )


def test_java_method_markers():

    code = (
        "public void create() {\n"
        "}\n"
        "\n"
        "private void delete() {\n"
        "}\n"
    )

    chunker = CodeChunker(
        max_tokens=1
    )

    parts = chunker._split_structurally(
        code=code,
        language="java",
    )

    assert len(parts) == 2
    assert "".join(parts) == code


# =========================================================
# 10. RAW LINE SPLITTER
# =========================================================

def test_exactly_40_lines():

    code = "\n".join(
        f"line {i}"
        for i in range(40)
    )

    chunker = CodeChunker()

    parts = chunker._split_lines_raw(
        code,
        max_lines=40,
    )

    assert len(parts) == 1


def test_41_lines():

    code = "\n".join(
        f"line {i}"
        for i in range(41)
    )

    chunker = CodeChunker()

    parts = chunker._split_lines_raw(
        code,
        max_lines=40,
    )

    assert len(parts) == 2


def test_80_lines():

    code = "\n".join(
        f"line {i}"
        for i in range(80)
    )

    chunker = CodeChunker()

    parts = chunker._split_lines_raw(
        code,
        max_lines=40,
    )

    assert len(parts) == 2


def test_81_lines():

    code = "\n".join(
        f"line {i}"
        for i in range(81)
    )

    chunker = CodeChunker()

    parts = chunker._split_lines_raw(
        code,
        max_lines=40,
    )

    assert len(parts) == 3


# =========================================================
# 11. NO-PROGRESS / HUGE SINGLE LINE
# =========================================================

def test_huge_single_line_does_not_crash():

    code = "x = " + ("a" * 50_000)

    chunker = CodeChunker(
        max_tokens=100
    )

    assert chunker._fits(code) is False

    routed_chunk = make_routed_chunk(
        code=code,
        language="python",
    )

    result = chunker.chunk(routed_chunk)

    assert len(result) == 1
    assert result[0].text == code


def test_huge_unsupported_language_does_not_crash():

    code = "x = " + ("a" * 50_000)

    chunker = CodeChunker(
        max_tokens=100
    )

    routed_chunk = make_routed_chunk(
        code=code,
        language="rust",
    )

    result = chunker.chunk(routed_chunk)

    assert len(result) == 1
    assert result[0].text == code


# =========================================================
# 12. CONTENT PRESERVATION
# =========================================================

def test_structural_split_preserves_exact_source():

    code = (
        "class A:\n"
        "    pass\n"
        "\n"
        "class B:\n"
        "    pass\n"
        "\n"
        "def hello():\n"
        "    return 'hello'\n"
    )

    chunker = CodeChunker()

    parts = chunker._split_structurally(
        code=code,
        language="python",
    )

    assert "".join(parts) == code


def test_line_split_preserves_exact_source():

    code = "\n".join(
        f"line {i}"
        for i in range(100)
    )

    chunker = CodeChunker()

    parts = chunker._split_lines_raw(
        code,
        max_lines=40,
    )

    assert "\n".join(parts) == code


def test_special_characters_are_preserved():

    code = (
        'message = "hello\\nworld"\n'
        'value = {"a": [1, 2, 3]}\n'
        "path = 'C:\\\\Users\\\\test'\n"
        "emoji = '🚀'\n"
    )

    chunker = CodeChunker(
        max_tokens=1000
    )

    routed_chunk = make_routed_chunk(
        code=code
    )

    result = chunker.chunk(routed_chunk)

    assert len(result) == 1
    assert result[0].text == code


# =========================================================
# 13. METADATA
# =========================================================

def test_language_metadata_is_preserved():

    code = (
        "def hello():\n"
        "    return 1"
    )

    routed_chunk = make_routed_chunk(
        code=code,
        language="python",
    )

    chunker = CodeChunker()

    result = chunker.chunk(routed_chunk)

    assert result[0].metadata["language"] == "python"


def test_existing_metadata_is_preserved():

    code = (
        "def hello():\n"
        "    return 1"
    )

    metadata = {
        "language": "python",
        "doc_id": "doc-123",
        "filename": "example.py",
        "detected_via": "fence",
    }

    routed_chunk = make_routed_chunk(
        code=code,
        language="python",
        metadata=metadata,
    )

    chunker = CodeChunker()

    result = chunker.chunk(routed_chunk)

    assert result[0].metadata["doc_id"] == "doc-123"
    assert result[0].metadata["filename"] == "example.py"
    assert result[0].metadata["detected_via"] == "fence"


def test_section_path_is_preserved():

    code = (
        "def authenticate():\n"
        "    return True"
    )

    section_path = [
        "Chapter 2",
        "Implementation",
        "Authentication",
    ]

    routed_chunk = make_routed_chunk(
        code=code,
        section_path=section_path,
    )

    chunker = CodeChunker()

    result = chunker.chunk(routed_chunk)

    assert result[0].metadata["section_path"] == section_path


def test_order_index_is_preserved():

    code = (
        "def authenticate():\n"
        "    return True"
    )

    routed_chunk = make_routed_chunk(
        code=code,
        order_index=42,
    )

    chunker = CodeChunker()

    result = chunker.chunk(routed_chunk)

    assert result[0].elements[0].order_index == 42


# =========================================================
# 14. WHITESPACE / INDENTATION
# =========================================================

def test_python_indentation_is_preserved():

    code = (
        "def foo():\n"
        "    if True:\n"
        "        print('hello')\n"
        "    return 1\n"
    )

    chunker = CodeChunker()

    routed_chunk = make_routed_chunk(
        code=code
    )

    result = chunker.chunk(routed_chunk)

    assert result[0].text == code


def test_tabs_are_preserved():

    code = (
        "\tdef foo():\n"
        "\t\treturn 1\n"
    )

    chunker = CodeChunker()

    routed_chunk = make_routed_chunk(
        code=code
    )

    result = chunker.chunk(routed_chunk)

    assert result[0].text == code


def test_blank_lines_are_preserved():

    code = (
        "class A:\n"
        "\n"
        "\n"
        "    def foo(self):\n"
        "        return 1\n"
    )

    chunker = CodeChunker()

    routed_chunk = make_routed_chunk(
        code=code
    )

    result = chunker.chunk(routed_chunk)

    assert result[0].text == code


# =========================================================
# 15. FINAL END-TO-END CHUNK TEST
# =========================================================

def test_large_python_code_is_split_and_preserved():

    functions = []

    for i in range(20):

        functions.append(
            f"def function_{i}():\n"
            f"    value = {i}\n"
            f"    return value\n"
        )

    code = "\n".join(functions)

    chunker = CodeChunker(
        max_tokens=20
    )

    routed_chunk = make_routed_chunk(
        code=code,
        language="python",
        order_index=42,
    )

    result = chunker.chunk(routed_chunk)

    assert len(result) > 1

    reconstructed = "".join(
        chunk.text
        for chunk in result
    )

    assert reconstructed == code

    for chunk in result:

        assert isinstance(
            chunk,
            CodeChunk,
        )

        assert (
            chunk.elements[0].order_index
            == 42
        )

        assert (
            chunk.metadata["language"]
            == "python"
        )