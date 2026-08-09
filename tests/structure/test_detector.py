from app.services.chunking.structure_detection.detector import StructureDetector
from app.services.chunking.structure_detection.models import StructureType, StructureScores
from app.dto.extracted_element import ExtractedElement
from app.dto.extraction_result import ExtractionResult
from app.enums.element_type import ElementType


def make_result(elements):
    return ExtractionResult(elements=elements)


def heading(text, level):
    return ExtractedElement(
        order_index=0,
        text=text,
        element_type=ElementType.HEADING,
        metadata={"level": level},
    )


def paragraph(text):
    return ExtractedElement(
        order_index=0,
        text=text,
        element_type=ElementType.PARAGRAPH,
        metadata={},
    )


def table(text="Table content"):
    return ExtractedElement(
        order_index=0,
        text=text,
        element_type=ElementType.TABLE,
        metadata={},
    )


def list_item(text):
    return ExtractedElement(
        order_index=0,
        text=text,
        element_type=ElementType.LIST,
        metadata={},
    )


# ============================================================
# 1. EMPTY DOCUMENT
# ============================================================

def test_empty_document():

    result = make_result([])

    detector = StructureDetector()
    detection = detector.detect(result)

    assert detection.structure_type == StructureType.UNSTRUCTURED


# ============================================================
# 2. ONLY PARAGRAPHS
# ============================================================

def test_only_paragraphs():

    elements = [
        paragraph("This is paragraph one."),
        paragraph("This is paragraph two."),
        paragraph("This is paragraph three."),
    ]

    result = make_result(elements)

    detector = StructureDetector()
    detection = detector.detect(result)

    assert detection.structure_type == StructureType.UNSTRUCTURED


# ============================================================
# 3. TECHNICAL REPORT
# ============================================================

def test_technical_report():

    elements = [
        heading("Introduction", 1),
        paragraph("This introduces the system."),
        heading("Architecture", 2),
        paragraph("The architecture contains several components."),
        table("Component | Description"),
        heading("Implementation", 2),
        paragraph("Implementation details."),
    ]

    result = make_result(elements)

    detector = StructureDetector()
    detection = detector.detect(result)

    assert detection.structure_type == StructureType.STRUCTURED


# ============================================================
# 4. CSV-LIKE DOCUMENT
# ============================================================

def test_csv_like_document():

    elements = [
        table("Name | Age | City"),
        table("Abhishek | 20 | Mumbai"),
        table("Rahul | 21 | Pune"),
        table("John | 22 | Delhi"),
    ]

    result = make_result(elements)

    detector = StructureDetector()
    detection = detector.detect(result)

    assert detection.structure_type == StructureType.TABULAR


# ============================================================
# 5. MEETING NOTES
# ============================================================

def test_meeting_notes():

    elements = [
        paragraph("Meeting started at 10 AM."),
        paragraph("Discussed project progress."),
        list_item("Complete backend API."),
        paragraph("Next meeting is Friday."),
    ]

    result = make_result(elements)

    detector = StructureDetector()
    detection = detector.detect(result)

    assert detection.structure_type == StructureType.UNSTRUCTURED


# ============================================================
# 6. STRUCTURED DOCUMENT WITH MANY TABLES
# ============================================================

def test_thin_document_with_one_heading_and_tables():

    elements = [
        heading("System Overview", 1),
        paragraph("The system provides enterprise knowledge management."),
        paragraph("It supports multiple document types."),
        table("Component | Technology"),
        table("API | FastAPI"),
        paragraph("The following section describes deployment."),
    ]

    result = make_result(elements)

    detector = StructureDetector()
    detection = detector.detect(result)

    assert detection.structure_type == StructureType.UNSTRUCTURED


# ============================================================
# ROUTING LOGIC TESTS
# ============================================================

def test_tabular_dominance():

    detector = StructureDetector()

    scores = StructureScores(
        structured=0.10,
        unstructured=0.20,
        tabular=0.80,
    )

    result = detector._determine_structure_type(scores,heading_count=0)

    assert result == StructureType.TABULAR


def test_structured_suppresses_tabular():

    detector = StructureDetector()

    scores = StructureScores(
        structured=0.80,
        unstructured=0.20,
        tabular=0.80,
    )

    result = detector._determine_structure_type(scores,heading_count=2)

    assert result == StructureType.STRUCTURED


def test_unstructured_routing():

    detector = StructureDetector()

    scores = StructureScores(
        structured=0.20,
        unstructured=0.70,
        tabular=0.30,
    )

    result = detector._determine_structure_type(scores,heading_count=0)

    assert result == StructureType.UNSTRUCTURED

def test_technical_report_with_many_tables():

    elements = []

    # 10 reasonably nested headings
    heading_levels = [1, 2, 3, 3, 2, 2, 3, 3, 2, 3]

    for i, level in enumerate(heading_levels):
        elements.append(
            heading(f"Section {i + 1}", level)
        )

    # 15 paragraphs
    for i in range(15):
        elements.append(
            paragraph(f"Technical report paragraph {i + 1}.")
        )

    # 12 tables
    for i in range(12):
        elements.append(
            table(f"Table {i + 1}")
        )

    result = make_result(elements)

    detector = StructureDetector()
    detection = detector.detect(result)

    assert len(elements) == 37
    assert detection.scores.structured >= 0.35
    assert detection.scores.tabular < 0.50
    assert detection.structure_type == StructureType.STRUCTURED

def test_two_headings_is_structured_eligible():

    elements = [
        heading("Introduction", 1),
        paragraph("Introduction content."),
        heading("Architecture", 2),
        paragraph("Architecture content."),
    ]

    result = make_result(elements)

    detector = StructureDetector()
    detection = detector.detect(result)

    assert detection.structure_type == StructureType.STRUCTURED