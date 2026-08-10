from dataclasses import dataclass, field
from typing import Any

from app.dto.extracted_element import ExtractedElement

@dataclass
class ChunkCandidate:

    text: str

    elements: list[ExtractedElement]

    heading: str | None

    section_path: list[str]

    metadata: dict[str, Any] = field(default_factory=dict)