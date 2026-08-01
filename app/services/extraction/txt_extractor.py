from pathlib import Path
import re

from app.dto.extracted_element import ExtractedElement
from app.dto.extraction_result import ExtractionResult
from app.enums.element_type import ElementType
from app.services.extraction.base_extractor import BaseExtractor

class TxtExtractor(BaseExtractor):

    def extract(self, file_path:str | Path)-> ExtractionResult:

        text = Path(file_path).read_text(encoding="utf-8") #Read the file

        text = text.replace("\r\n", "\n").replace("\r","\n")

        paragraphs = re.split(r"\n\s*\n",text)

        elements = []

        for order_index, paragraph in enumerate(paragraphs):

            paragraph = paragraph.strip()

            if not paragraph:
                continue

            elements.append(
                ExtractedElement(
                    order_index=order_index,
                    text=paragraph,
                    element_type=ElementType.PARAGRAPH,
                    metadata={
                        "source":"txt"
                    }
                )
            )
        return ExtractionResult(
            elements=elements
        )






