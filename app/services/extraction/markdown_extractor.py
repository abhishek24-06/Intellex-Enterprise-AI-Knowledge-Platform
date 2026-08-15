from pathlib import Path
from markdown_it import MarkdownIt
from markdown_it.token import Token
from typing import Any
from app.dto.extracted_element import ExtractedElement
from app.dto.extraction_result import ExtractionResult
from app.services.extraction.base_extractor import BaseExtractor
from app.enums.element_type import ElementType

class MarkdownExtractor(BaseExtractor):

    def __init__(self):

        self.md = MarkdownIt("commonmark").enable("table")

    def extract(self,file_path:str | Path,
                document_id:str |None=None,filename:str |None=None)->ExtractionResult:

        filename = filename or Path(file_path).name

        text = Path(file_path).read_text(encoding="utf-8")

        tokens = self.md.parse(text) #.parse reads the md text and convert to structured tokens

        elements = []

        order_index=0
        table_index=0
        i = 0

        while i < len(tokens):
            token = tokens[i] 

            #HEADING
            if token.type == "heading_open":

                element, i = self._extract_heading(
                    tokens=tokens,
                    index=i,
                    order_index=order_index,
                    document_id=document_id,
                    filename=filename
                )

                elements.append(element)

                order_index +=1
                continue

            #PARAGRAPHS
            elif token.type == "paragraph_open":

                element, i = self._extract_paragraph(
                    tokens=tokens,
                    index=i,
                    order_index=order_index,
                    document_id=document_id,
                    filename=filename
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
                    order_index=order_index,
                    document_id=document_id,
                    filename=filename
                )
                elements.extend(list_elements)

                order_index += len(list_elements)
                continue

            elif token.type == "blockquote_open":

                element,i = self._extract_quote(
                    index=i,
                    tokens=tokens,
                    order_index=order_index,
                    document_id=document_id,
                    filename=filename
                )

                elements.append(element)

                order_index += 1
                continue

            elif token.type == "fence":

                element,i = self._extract_code_block(
                    tokens=tokens,
                    index=i,
                    order_index=order_index,
                    document_id=document_id,
                    filename=filename
                )

                elements.append(element)

                order_index +=1
                continue

            elif token.type == "table_open":

                element, i = self._extract_table(
                    tokens=tokens,
                    index=i,
                    order_index=order_index,
                    table_index=table_index,
                    document_id=document_id,
                    filename=filename
                )

                elements.append(element)
                table_index += 1
                order_index += 1
                continue
            
            else:
                i += 1

        return ExtractionResult(elements=elements)

    def _extract_heading(self,tokens: list[Token],index:int,order_index:int,
                document_id:str |None=None,filename:str |None=None)->tuple[ExtractedElement,int]:

        opening_token = tokens[index]
        inline_token = tokens[index+1]

        level = int(opening_token.tag[1])

        element = ExtractedElement(
            order_index=order_index,
            text=inline_token.content,
            element_type=ElementType.HEADING,
            metadata={
                **self._base_metadata(
                    document_id=document_id,
                    filename=filename
                ),
                "source": "markdown",
                "level": level
            }
        )
        return element, index+3

    def _extract_paragraph(self,tokens: list[Token],index:int,order_index:int,
                document_id:str |None=None,filename:str |None=None)-> tuple[ExtractedElement,int]:

        inline_token = tokens[index+1]

        element = ExtractedElement(
            order_index=order_index,
            text=inline_token.content,
            element_type=ElementType.PARAGRAPH,
            metadata={
                **self._base_metadata(
                    document_id=document_id,
                    filename=filename
                ),
                "source": "markdown",
            }
        )

        return element, index + 3

    def _extract_list(self,tokens: list[Token],index:int,order_index:int,ordered:bool,depth:int = 0,
                document_id:str |None=None,filename:str |None=None)->tuple[list[ExtractedElement], int]:

        elements = []

        closing_token = (
            "ordered_list_close"
            if ordered
            else "bullet_list_close"
        )

        start_index = index
        index +=1 # Skip *_list_open

        while index < len(tokens):

            token = tokens[index]

            if (token.type in ("ordered_list_open","bullet_list_open")
                              and index > start_index):

                nested_ordered = (token.type == "ordered_list_open")
            
                nested_elements, index = self._extract_list(
                    tokens=tokens,
                    index=index,
                    order_index=order_index + len(elements),
                    ordered=nested_ordered,
                    depth=depth + 1,
                    document_id=document_id,
                    filename=filename
                )
                elements.extend(nested_elements)
                continue

            if token.type == closing_token:
                return elements,index +1

            if token.type == "inline":

                elements.append(
                    ExtractedElement(
                        order_index=order_index + len(elements),
                        text=token.content,
                        element_type=ElementType.LIST,
                        metadata={
                            **self._base_metadata(
                                document_id=document_id,
                                filename=filename
                            ),
                            "source": "markdown",
                            "ordered":ordered,
                            "indent_level": depth
                        }
                    )
                )
            index +=1

        return elements, index

    def _extract_quote(self,tokens:list[Token],index:int,order_index:int,
                document_id:str |None=None,filename:str |None=None)-> tuple[ExtractedElement, int]:

        quote_lines = []
        depth = 1
        index += 1 #Skip blockquote_open

        while index < len(tokens):
            token = tokens[index]

            if token.type == "blockquote_open":
                depth +=1

            elif token.type == "blockquote_close":
                depth -= 1

                if depth == 0:
                    index += 1
                    break

            elif token.type == "inline":
                quote_lines.append(token.content)

            index += 1

        element = ExtractedElement(
            order_index=order_index,
            text="\n".join(quote_lines),
            element_type=ElementType.QUOTE,
            metadata={
                **self._base_metadata(
                    document_id=document_id,
                    filename=filename
                ),
                "source": "markdown",
            }
        )

        return element, index

    def _extract_code_block(self,tokens:list[Token],index:int,order_index:int,
                document_id:str |None=None,filename:str |None=None)->tuple[ExtractedElement,int]:

        token = tokens[index]

        element = ExtractedElement(
            order_index=order_index,
            text=token.content,
            element_type=ElementType.CODE_BLOCK,
            metadata={
                **self._base_metadata(
                    document_id=document_id,
                    filename=filename
                ),
                "source": "markdown",
                "language": token.info.strip() or None
            }
        )

        return element, index +1

    def _looks_like_header_row(self,row_cells:list[str])->bool:

        if not row_cells:
            return False

        non_numeric = sum(
            1
            for cell in row_cells
            if cell
            and not cell.replace(".", "").replace(",", "").isdigit())

        return non_numeric / len(row_cells) >= 0.7

    def _extract_table_metadata(self,rows_data:list[list[str]],table_index: int,
                document_id:str |None=None,filename:str |None=None)->dict[str,Any]:

        has_header_row = (self._looks_like_header_row(rows_data[0])
                        if rows_data
                        else False)

        table_id = (
            f"{document_id}-table-{table_index}"
            if document_id
            else f"table-{table_index}"
            )

        return {
            "table_id": table_id,
            "table_index": table_index,
            "n_rows": len(rows_data),
            "n_cols": max((len(row) for row in rows_data),default=0,),
            "cells": rows_data,
            "has_header_row": has_header_row,
            "markdown": self._table_to_markdown(rows_data,has_header_row,),
            }

    def _extract_table(self,tokens:list[Token],index:int,order_index:int,table_index: int,
                document_id:str |None=None,filename:str |None=None)-> tuple[ExtractedElement, int]:

        rows_data: list[list[str]] = []
        current_row: list[str] = []

        index += 1 #Skip table_open

        while index < len(tokens):
            token = tokens[index]

            if token.type == "table_close":
                text = "\n".join(
                    " | ".join(row)
                    for row in rows_data
                )
                element = ExtractedElement(
                    order_index=order_index,
                    text=text,
                    element_type=ElementType.TABLE,
                    metadata={
                        **self._base_metadata(
                            document_id=document_id,
                            filename=filename
                        ),
                        "source": "markdown",
                        **self._extract_table_metadata(rows_data,table_index,document_id,filename)
                }
            )

                return element, index+1

            elif token.type == "tr_open":

                current_row = []

            elif token.type == "inline":

                current_row.append(token.content)

            elif token.type == "tr_close":

                rows_data.append(current_row)

            index += 1

        text = "\n".join(
            " | ".join(row)
            for row in rows_data
        )

        element = ExtractedElement(
            order_index=order_index,
            text=text,
            element_type=ElementType.TABLE,
            metadata={
                **self._base_metadata(
                    document_id=document_id,
                    filename=filename
                ),
                "source": "markdown",
                **self._extract_table_metadata(rows_data,table_index,document_id,filename)
            }
        )

        return element, index
    

    

    


