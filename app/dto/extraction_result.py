from dataclasses import dataclass

from app.dto.extracted_element import ExtractedElement

@dataclass(slots=True)
class ExtractionResult:
    elements: list[ExtractedElement]