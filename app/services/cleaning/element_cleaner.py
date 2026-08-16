import re

from app.dto.extracted_element import ExtractedElement
from app.dto.extraction_result import ExtractionResult
from app.enums.element_type import ElementType

class ElementCleaner:

    NARRATIVE_TYPES = {
        ElementType.TITLE,
        ElementType.HEADING,
        ElementType.PARAGRAPH,
        ElementType.LIST,
        ElementType.QUOTE,
        ElementType.CAPTION,
        ElementType.UNKNOWN,
        ElementType.IMAGE
    }

    CODE_TYPES = {
        ElementType.CODE_BLOCK,
    }

    TABLE_TYPES = {
        ElementType.TABLE,
    }

    def clean(self,extraction_result:ExtractionResult)->ExtractionResult:

        if not isinstance(extraction_result,ExtractionResult):
            raise TypeError("Expected extraction_result to be an ExtractionResult.")

        cleaned_elements = [self._clean_element(element)
                            for element in extraction_result.elements]

        return ExtractionResult(elements=cleaned_elements)

    def _clean_element(self,element:ExtractedElement)->ExtractedElement:

        if not isinstance(element,ExtractedElement):
            raise TypeError("Expected element to be an ExtractedElement.")

        text = element.text

        if not isinstance(text, str):
            raise TypeError("ExtractedElement.text must be a string.")

        if element.element_type in self.CODE_TYPES:
            cleaned_text = self._clean_code(text)

        elif element.element_type in self.TABLE_TYPES:
            cleaned_text = self._clean_table(text)

        else:
            cleaned_text = self._clean_narrative(text)

        return ExtractedElement(
            order_index=element.order_index,
            text=cleaned_text,
            element_type=element.element_type,
            metadata=dict(element.metadata),
        )

    def _clean_narrative(self,text:str)->str:

        text = self._normalize_line_endings(text)

        text = self._remove_trailing_whitespace(text)

        text = self._collapse_tabs(text)

        text = self._collapse_blank_lines(text)

        return text.strip()

    def _clean_code(self,text:str) -> str:

        return self._normalize_line_endings(text)

    def _clean_table(self,text:str) -> str:

        text = self._normalize_line_endings(text)

        return self._remove_trailing_whitespace(text)

    @staticmethod
    def _normalize_line_endings(text:str)->str:
        return(text.replace('\r\n','\n').replace('\r','\n'))

    @staticmethod
    def _remove_trailing_whitespace(text:str) -> str:
        return "\n".join(
            line.rstrip()
            for line in text.split("\n")
        )

    @staticmethod
    def _collapse_tabs(text:str) -> str:
        return re.sub(
            r"\t+",
            " ",
            text,
        )

    @staticmethod
    def _collapse_blank_lines(text:str) -> str:
        return re.sub(
            r"\n{3,}",
            "\n\n",
            text,
        )
