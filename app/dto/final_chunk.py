from dataclasses import dataclass, field
from typing import Any

from app.dto.extracted_element import ExtractedElement
from app.enums.chunk_type import ChunkType

@dataclass
class FinalChunk:

    text: str
    elements: list[ExtractedElement]
    chunk_type: ChunkType
    section_path: list[str]
    order_index: int
    metadata: dict[str,Any] = field(default_factory=dict)
     