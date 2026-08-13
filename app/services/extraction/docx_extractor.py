from collections.abc import Iterator
from typing import Any
from docx import Document as DocxDocument
from docx.document import Document
from docx.table import Table
from docx.text.paragraph import Paragraph
import re
from pathlib import Path

from docx.oxml.text.paragraph import CT_P
from docx.oxml.table import CT_Tbl

from app.dto.extracted_element import ExtractedElement
from app.enums.element_type import ElementType
from app.services.extraction.base_extractor import BaseExtractor
from app.dto.extraction_result import ExtractionResult

HEADING_PATTERN = re.compile(r"heading\s+(\d+)",re.IGNORECASE)

CODE_STYLE_NAMES = {
    "code",
    "source code",
    "html code",
    "macro text",
}

MONOSPACE_FONTS = {
    "courier new",
    "consolas",
    "monaco",
    "menlo",
    "source code pro",
    "fira code",
}

class DocxExtractor(BaseExtractor):

    def extract(self,file_path:str,
                document_id:str |None=None,filename:str |None=None)->ExtractionResult:

        self.document_id = document_id
        self.filename = filename or Path(file_path).name
        self.table_index = 0

        doc = DocxDocument(file_path)

        elements=[]

        for order_index, block in enumerate(self._iter_block_items(doc)):

            element = None

            if isinstance(block,Paragraph): #Is this block a paragraph
                element = self._extract_paragraph(block,order_index)

            elif isinstance(block,Table):
                element = self._extract_table(table=block,order_index=order_index,table_index=self.table_index)
                self.table_index += 1

            if element is not None:
                elements.append(element)

        return ExtractionResult(elements=elements)

    def _iter_block_items(self,document:Document)->Iterator[Paragraph|Table]:

        body=document.element.body

        for child in body.iterchildren(): #Moves through every child i.e heading,para,table etc one by one in order

            if isinstance(child,CT_P): #Checks if child is Para(CT_P)
                yield Paragraph(child,document) #yield returns one child at a time

            elif isinstance(child,CT_Tbl): #Checks if child is Table
                yield Table(child,document)

    def _map_paragraph_style(self,paragraph:Paragraph)->tuple[ElementType,dict[str,Any]]:

        style_name=paragraph.style.name #Get style used
        style = re.sub(r"\s+", " ", style_name.lower()).strip() #lowerdcase the style

        metadata:dict[str,Any] = {"style":style_name}

        if style == "title":
            return ElementType.TITLE,metadata

        if style.startswith("heading"):
            metadata.update({
                "level":self._extract_heading_level(style), #adds heading level i.e(1,2,3)
                "numbering":self._extract_heading_numbering(paragraph), #adds sub headers number i.e(1.1,1.2,1.3)
           
            })

            return ElementType.HEADING,metadata

        if "quote" in style :
            return ElementType.QUOTE,metadata

        if (self._is_list_item(paragraph) or style.startswith("list")):
            metadata.update(
                self._extract_list_metadata(paragraph)
            )
            return ElementType.LIST, metadata

        if self._has_semantic_code_style(style_name):
            metadata["code_style"] = style_name
            metadata["detected_via"] = "style"

            return ElementType.CODE_BLOCK, metadata

        if self._looks_like_code_by_font(paragraph):
            metadata["detected_via"] = "font"

            return ElementType.CODE_BLOCK, metadata

        return ElementType.PARAGRAPH, metadata

    def _extract_heading_level(self,style:str)->int|None: #Extracts heading lvl eg 1 2 3 


        match = HEADING_PATTERN.search(style)

        if match:
            return int(match.group(1))

        return None
    
    def _is_list_item(self,paragraph:Paragraph)->bool: #Check if a para is List

        paragraph_properties = paragraph._p.pPr #Variable now contains paragraph properties

        return (
            paragraph_properties is not None #Check if para has properties
            and paragraph_properties.numPr is not None #Check if para has numbering properties 
        )

    def _extract_list_metadata(self,paragraph:Paragraph)->dict[str,Any]: #Checks if list is numbered or has bullets

        style = paragraph.style.name.lower()

        if style.startswith("list bullet"):
            ordered = False
        elif style.startswith("list number"):
            ordered = True
        else:  
            ordered = None

        return{
            "ordered":ordered
        }

    def _extract_heading_numbering(self,paragraph:Paragraph)->dict[str,Any]:

        paragraph_properties = paragraph._p.pPr

        has_num_pr=(
            paragraph_properties is not None
            and paragraph_properties.numPr is not None
        )

        return{
            "has_num_pr": has_num_pr,
            "resolved": False,
            "value": None
        }

    def _extract_paragraph(self,paragraph:Paragraph,order_index:int)->ExtractedElement|None:

        if not paragraph.text.strip(): #Checks if para is empty or only spaces, then None
            return None

        element_type, metadata = self._map_paragraph_style(paragraph)

        metadata = {
            **self._base_metadata(),
            "source": "docx",
            **metadata,
            }

        print(
        f"ORDER={order_index} | "
        f"STYLE={paragraph.style.name!r} | "
        f"TEXT={paragraph.text[:100]!r}"
    )
        
        return ExtractedElement(
            order_index=order_index,
            text= paragraph.text.strip(),
            element_type=element_type,
            metadata=metadata
        )

#TABLE
    def _table_to_text(self,table:Table)-> str:

        rows = []

        for row in table.rows:

            cells = [
                cell.text.strip()
                for cell in row.cells
            ]

            rows.append(" | ".join(cells))

        return "\n".join(rows)

    def _looks_like_header_row(self,row_cells:list[str])->bool:

        if not row_cells:
            return False

        non_numeric = sum(
            1
            for cell in row_cells
            if cell
            and not cell.replace(".", "").replace(",", "").isdigit())

        return non_numeric / len(row_cells) >= 0.7

    def _extract_table_metadata(self,table:Table,table_index:int)->dict[str,Any]:

        rows_data = [[
            cell.text.strip()
            for cell in row.cells
        ]
        for row in table.rows
        ]

        has_header_row = (self._looks_like_header_row(rows_data[0])
                        if rows_data
                        else False)

        return {
            **self._base_metadata(),
            "source": "docx",
            "table_id": (f"{self.document_id}-table-{table_index}"
                         if self.document_id
                         else f"table-{table_index}"),
            "n_rows": len(rows_data),
            "n_cols": max((len(row) for row in rows_data),default=0 ),
            "cells": rows_data,
            "has_header_row": has_header_row,
            "markdown": self._table_to_markdown(rows_data,has_header_row)
            }

    def _extract_table(self,table:Table,order_index:int,table_index:int)->ExtractedElement | None:

        text = self._table_to_text(table)

        if not text.strip():
            return None

        return ExtractedElement(
            order_index=order_index,
            text=text,
            element_type=ElementType.TABLE,
            metadata=self._extract_table_metadata(table,table_index)
        )

#CODE

    def _has_semantic_code_style(self, style_name: str) -> bool:

        return (style_name.strip().lower()
                in CODE_STYLE_NAMES
        )

    def _looks_like_code_by_font(self, paragraph: Paragraph) -> bool:

        runs = [run
                for run in paragraph.runs
                if run.text.strip()
        ]
    
        if not runs:
            return False
    
        monospace_runs = sum(1
                for run in runs
                if (
                    run.font.name
                    and run.font.name.strip().lower()
                    in MONOSPACE_FONTS
                )
        )
    
        return monospace_runs / len(runs) >= 0.7
