from dataclasses import dataclass
from typing import Any

from app.dto.extracted_element import ExtractedElement


@dataclass
class TableChunk:

    text: str

    elements: list[ExtractedElement]

    metadata: dict[str, Any]