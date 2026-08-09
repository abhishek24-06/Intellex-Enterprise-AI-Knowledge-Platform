import pytest

from app.dto.extracted_element import ExtractedElement
from app.dto.extraction_result import ExtractionResult
from app.enums.element_type import ElementType
from app.services.chunking.structure_detection.scoring import StructureScorer


def make_element(
    element_type: ElementType,
    level: int | None = None,
    order_index: int = 0,
) -> ExtractedElement:

    metadata = {}

    if level is not None:
        metadata["level"] = level

    return ExtractedElement(
        order_index=order_index,
        text="Dummy",
        element_type=element_type,
        metadata=metadata,
    )

def test_empty_extraction():

    scorer = StructureScorer()

    result = ExtractionResult(
        elements=[]
    )

    scores = scorer.score(result)

    assert scores.structured == 0.0
    assert scores.unstructured == 1.0
    assert scores.tabular == 0.0


def test_only_paragraphs():

    scorer = StructureScorer()

    result = ExtractionResult(
        elements=[
            make_element(ElementType.PARAGRAPH),
            make_element(ElementType.PARAGRAPH),
            make_element(ElementType.PARAGRAPH),
        ]
    )

    scores = scorer.score(result)

    assert scores.structured == 0.175
    assert scores.tabular == 0.0
    assert scores.unstructured == 0.825

def test_heading_and_paragraphs():

    scorer = StructureScorer()

    result = ExtractionResult(
        elements=[
            make_element(ElementType.HEADING, level=1),
            make_element(ElementType.PARAGRAPH),
            make_element(ElementType.PARAGRAPH),
        ]
    )

    scores = scorer.score(result)

    expected_structured = (
        (1 / 3) * scorer.HEADING_WEIGHT
        + 0.5 * scorer.HIERARCHY_WEIGHT
        + 0.0 * scorer.LIST_WEIGHT
    )

    assert scores.structured == expected_structured
    assert scores.tabular == 0.0
    assert scores.unstructured == 1.0 - expected_structured

def test_perfect_heading_hierarchy():

    scorer = StructureScorer()

    result = ExtractionResult(
        elements=[
            make_element(ElementType.HEADING, level=1),
            make_element(ElementType.HEADING, level=2),
            make_element(ElementType.HEADING, level=2),
            make_element(ElementType.HEADING, level=3),
        ]
    )

    scores = scorer.score(result)

    expected_structured = (
        (4 / 4) * scorer.HEADING_WEIGHT
        + 1.0 * scorer.HIERARCHY_WEIGHT
        + 0.0 * scorer.LIST_WEIGHT
    )

    assert scores.structured == expected_structured
    assert scores.tabular == 0.0
    assert scores.unstructured == 1.0 - expected_structured

def test_invalid_heading_hierarchy():

    scorer = StructureScorer()

    result = ExtractionResult(
        elements=[
            make_element(ElementType.HEADING, level=1),
            make_element(ElementType.HEADING, level=4),
            make_element(ElementType.HEADING, level=2),
        ]
    )

    scores = scorer.score(result)

    expected_hierarchy = 0.5  # 1 valid transition out of 2

    expected_structured = (
        1.0 * scorer.HEADING_WEIGHT
        + expected_hierarchy * scorer.HIERARCHY_WEIGHT
        + 0.0 * scorer.LIST_WEIGHT
    )

    assert scores.structured == pytest.approx(expected_structured)
    assert scores.tabular == 0.0
    assert scores.unstructured == pytest.approx(1.0 - expected_structured)

def test_table_only_document():

    scorer = StructureScorer()

    result = ExtractionResult(
        elements=[
            make_element(ElementType.TABLE),
            make_element(ElementType.TABLE),
            make_element(ElementType.TABLE),
        ]
    )

    scores = scorer.score(result)

    assert scores.structured == pytest.approx(0.175)
    assert scores.tabular == pytest.approx(1.0)
    assert scores.unstructured == pytest.approx(0.0)

def test_list_only_document():

    scorer = StructureScorer()

    result = ExtractionResult(
        elements=[
            make_element(ElementType.LIST),
            make_element(ElementType.LIST),
            make_element(ElementType.LIST),
            make_element(ElementType.LIST),
        ]
    )

    scores = scorer.score(result)

    expected_structured = (
        0.0 * scorer.HEADING_WEIGHT
        + 0.5 * scorer.HIERARCHY_WEIGHT
        + 1.0 * scorer.LIST_WEIGHT
    )

    assert scores.structured == pytest.approx(expected_structured)
    assert scores.tabular == 0.0
    assert scores.unstructured == pytest.approx(1.0 - expected_structured)

def test_mixed_document():

    scorer = StructureScorer()

    result = ExtractionResult(
        elements=[
            make_element(ElementType.HEADING, level=1),
            make_element(ElementType.PARAGRAPH),
            make_element(ElementType.LIST),
            make_element(ElementType.TABLE),
            make_element(ElementType.PARAGRAPH),
        ]
    )

    scores = scorer.score(result)

    assert 0.0 <= scores.structured <= 1.0
    assert 0.0 <= scores.tabular <= 1.0
    assert 0.0 <= scores.unstructured <= 1.0