from pathlib import Path
from docling.document_converter import DocumentConverter

from app.enums.element_type import ElementType
from app.dto.extracted_element import ExtractedElement
from app.dto.extraction_result import ExtractionResult
from app.services.extraction.base_extractor import BaseExtractor

class DoclingExtractor(BaseExtractor):

    def __init__(self):

        self.converter = DocumentConverter()
        
    def extract(self,file_path: str | Path,
                document_id:str |None=None,filename:str |None=None)-> ExtractionResult:

        filename = filename or Path(file_path).name      

        result = self.converter.convert(str(file_path))

        document = result.document
        
        table_index = 0

        elements: list[ExtractedElement] = []

        for order_index, (item, level ) in enumerate(document.iterate_items()):

            element = self._extract_element(
                    order_index=order_index, 
                    item=item,
                    level=level,
                    table_index=table_index,
                    document_id=document_id,
                    filename=filename)

            if element is not None:
                elements.append(element)

            if item.label == "table":
                table_index += 1

        return ExtractionResult(elements=elements)

    def _extract_element(self,item,level:int,order_index:int,table_index:int,
                document_id:str |None=None,filename:str |None=None)-> ExtractedElement | None:

        match item.label:

            case "section_header":
                return self._extract_heading(order_index=order_index, item=item, level=level,document_id=document_id,filename=filename)

            case "text":
                return self._extract_paragraph(order_index=order_index, item=item,document_id=document_id,filename=filename)

            case "table": 
                element = self._extract_table(order_index=order_index, item=item, table_index=table_index,document_id=document_id,filename=filename)
                return element

            case "picture":
                return self._extract_picture(order_index=order_index, item=item,document_id=document_id,filename=filename)

            case "list_item":
                return self._extract_list(order_index=order_index, item=item,document_id=document_id,filename=filename)

            case "code":
                return self._extract_code(order_index=order_index,item=item,document_id=document_id,filename=filename)
            
            case _:
                return None

    def _extract_provenance(self,item)->tuple[int, tuple[float, float, float, float]]:

        if not item.prov:
            return None,None
        
        prov = item.prov[0] #list contains info like page_no, bbox etc

        return (
            prov.page_no,
            (
                prov.bbox.l, #Left
                prov.bbox.t, #Top
                prov.bbox.r, #Right
                prov.bbox.b  #Bottom
            ),
        )
    
    def _extract_heading(self,item,level:int,order_index:int,document_id:int|None,filename:int|None)-> ExtractedElement:

        page, bbox = self._extract_provenance(item)

        return ExtractedElement(
            order_index=order_index,
            text=item.text,
            element_type=ElementType.HEADING,
            metadata={
                **self._base_metadata(
                    document_id=document_id,
                    filename=filename
                ),
                "page": page,
                "bbox": bbox,
                "level": level,
                "source": "docling"
            }
        )

    def _extract_paragraph(self,item,order_index:int,document_id:int|None,filename:int|None)-> ExtractedElement:

        page, bbox = self._extract_provenance(item)

        return  ExtractedElement(
            order_index=order_index,
            text=item.text,
            element_type=ElementType.PARAGRAPH,
            metadata={
                **self._base_metadata(
                    document_id=document_id,
                    filename=filename
                ),
                "page": page,
                "bbox": bbox,
                "source": "docling"
            }
        )

    def _extract_table(self,item,order_index:int,table_index:int,document_id:int|None,filename:int|None)-> ExtractedElement:

        table_id = (f"{document_id}-table-{table_index}"
                    if document_id
                    else f"table-{table_index}"
                   )

        page, bbox = self._extract_provenance(item)

        rows_data = [
            [""] *  item.data.num_cols # number of coln
            for _ in range(item.data.num_rows) #iterate = no of rows
        ]

        for cell in item.data.table_cells: # cell = every word in table

            rows_data[cell.start_row_offset_idx][cell.start_col_offset_idx] = cell.text #rows_data[0][0]=cell.text

        text = "\n".join(
            " | ".join(row)
            for row in rows_data
        )

        has_header_row = any(cell.column_header
                        for cell in item.data.table_cells)
        
        metadata = {
            **self._base_metadata(
                document_id=document_id,
                filename=filename
            ),
            "table_id": table_id,
            "table_index":table_index,
            "page": page,
            "bbox": bbox,
            "source": "docling",
            "cells": rows_data,
            "n_rows": item.data.num_rows,
            "n_cols": item.data.num_cols,
            "has_header_row": has_header_row,
            "markdown": self._table_to_markdown(rows_data,has_header_row)
        }

        return ExtractedElement(
            order_index=order_index,
            text=text,
            element_type=ElementType.TABLE,
            metadata=metadata,
        )

    def _extract_picture(self,item,order_index:int,document_id:int|None,filename:int|None)-> ExtractedElement:

        page, bbox = self._extract_provenance(item)

        return ExtractedElement(
            order_index=order_index,
            text="[IMAGE]",
            element_type=ElementType.IMAGE,
            metadata={
                **self._base_metadata(
                    document_id=document_id,
                    filename=filename
                ),
                "page": page,
                "bbox": bbox,
                "source":"docling"
            }
        )

    def _extract_list(self,item,order_index:int,document_id:int|None,filename:int|None)->ExtractedElement:

        page, bbox = self._extract_provenance(item)

        return ExtractedElement(
            order_index=order_index,
            text=item.text,
            element_type=ElementType.LIST,
            metadata={
                **self._base_metadata(
                    document_id=document_id,
                    filename=filename
                ),
                "page": page,
                "bbox": bbox,
                "source": "docling",
                "ordered": item.enumerated, #Tells if list is ordered/unordered
                "marker": item.marker #Store symbol Eg "-" for - Python
            }
        )

    def _extract_code(self,item,order_index:int,document_id:int|None,filename:int|None)->ExtractedElement:

        page,bbox = self._extract_provenance(item)

        return ExtractedElement(order_index=order_index,
                                text=item.text,
                                element_type=ElementType.CODE_BLOCK,
                                metadata={
                                    **self._base_metadata(
                                        document_id=document_id,
                                        filename=filename
                                    ),
                                    "page": page,
                                    "bbox": bbox,
                                    "source": "docling",
                                    "language": getattr(
                                        item,
                                        "code_language",
                                        None
                                    )
                                }
                                )