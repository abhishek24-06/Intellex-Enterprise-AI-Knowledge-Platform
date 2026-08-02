from pathlib import Path
from markdown_it import MarkdownIt
from markdown_it.token import Token

from app.dto.extracted_element import ExtractedElement
from app.dto.extraction_result import ExtractionResult
from app.services.extraction.base_extractor import BaseExtractor
from app.enums.element_type import ElementType

class MarkdownExtractor(BaseExtractor):

    def __init__(self):

        self.md = MarkdownIt("commonmark")

    def extract(self,file_path:str | Path)->ExtractionResult:

        text = Path(file_path).read_text(encoding="utf-8")

        tokens = self.md.parse(text) #.parse reads the md text and convert to structured tokens

        elements = []

        order_index=0
        i = 0

        while i < len(tokens):
            token = tokens[i] 

            #HEADING
            if token.type == "heading_open":

                element, i = self._extract_heading(
                    tokens=tokens,
                    index=i,
                    order_index=order_index
                )

                elements.append(element)

                order_index +=1
                continue

            #PARAGRAPHS
            elif token.type == "paragraph_open":

                element, i = self._extract_paragraph(
                    tokens=tokens,
                    index=i,
                    order_index=order_index
                )

                elements.append(element)

                order_index +=1
                continue

            # #LISTS
            elif token.type in ("bullet_list_open","ordered_list_open"):

                ordered = token.type == "ordered_list_open" #ordered is true if token.type is bullet_list_open else false

                list_elements, i = self._extract_list(
                    tokens=tokens,
                    index=i,
                    ordered=ordered,
                    order_index=order_index
                )
                elements.extend(list_elements)

                order_index += len(list_elements)
                continue

            elif token.type == "blockquote_open":

                element,i = self._extract_quote(
                    index=i,
                    tokens=tokens,
                    order_index=order_index
                )

                elements.append(element)

                order_index += 1
                continue

            elif token.type == "fence":

                element,i = self._extract_code_block(
                    tokens=tokens,
                    index=i,
                    order_index=order_index
                )

                elements.append(element)

                order_index +=1
                continue

            else:
                i += 1

        return ExtractionResult(elements=elements)

    def _extract_heading(self,tokens: list[Token],index:int,order_index:int)->tuple[ExtractedElement,int]:

        opening_token = tokens[index]
        inline_token = tokens[index+1]

        level = int(opening_token.tag[1])

        element = ExtractedElement(
            order_index=order_index,
            text=inline_token.content,
            element_type=ElementType.HEADING,
            metadata={
                "level": level
            }
        )
        return element, index+3

    def _extract_paragraph(self,tokens: list[Token],index:int,order_index:int)-> tuple[ExtractedElement,int]:

        inline_token = tokens[index+1]

        element = ExtractedElement(
            order_index=order_index,
            text=inline_token.content,
            element_type=ElementType.PARAGRAPH,
            metadata={}
        )

        return element, index + 3

    def _extract_list(self,tokens: list[Token],index:int,order_index:int,ordered:bool)->tuple[list[ExtractedElement], int]:

        elements = []

        closing_token = (
            "ordered_list_close"
            if ordered
            else "bullet_list_close"
        )

        index +=1 # Skip *_list_open

        while index < len(tokens):

            token = tokens[index]

            if token.type == closing_token:
                return elements,index +1

            if token.type == "inline":

                elements.append(
                    ExtractedElement(
                        order_index=order_index,
                        text=token.content,
                        element_type=ElementType.LIST,
                        metadata={
                            "ordered":ordered
                        }
                    )
                )
                order_index +=1
            index +=1

        return elements, index

    def _extract_quote(self,tokens:list[Token],index:int,order_index:int)-> tuple[ExtractedElement, int]:

        quote_lines = []
        index += 1 #Skip blockquote_open

        while index < len(tokens):
            token = tokens[index]

            if token.type == "blockquote_close":

                index += 1
                break

            if token.type == "inline":
                quote_lines.append(token.content)

            index += 1

        element = ExtractedElement(
            order_index=order_index,
            text="\n".join(quote_lines),
            element_type=ElementType.QUOTE,
            metadata={}
        )

        return element, index

    def _extract_code_block(self,tokens:list[Token],index:int,order_index:int)->tuple[ExtractedElement,int]:

        token = tokens[index]

        element = ExtractedElement(
            order_index=order_index,
            text=token.content,
            element_type=ElementType.CODE_BLOCK,
            metadata={
                "language": token.info.strip() or None
            }
        )

        return element, index +1
    

    

    


