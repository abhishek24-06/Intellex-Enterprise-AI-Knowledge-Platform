from dataclasses import dataclass

from app.dto.extracted_element import ExtractedElement
from app.enums.chunk_type import ChunkType

@dataclass
class RoutedChunk:

    chunk_type: ChunkType

    elements: list[ExtractedElement]

    text: str | None

    section_path: list[str]

    order_index: int