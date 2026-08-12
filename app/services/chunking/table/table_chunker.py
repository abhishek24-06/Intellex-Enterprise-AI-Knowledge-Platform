from app.dto.extracted_element import ExtractedElement
from app.dto.routed_chunk import RoutedChunk
from app.dto.table_chunk import TableChunk

class TableChunker:

    def __init__(self,max_tokens:int = 1000):
        self.max_tokens = max_tokens

    def chunk(self,routed_chunk: RoutedChunk)->list[TableChunk]:

        if not routed_chunk.elements: #checks if empty
            return []

        table_element = routed_chunk.elements[0] 

        cells  = table_element.metadata.get("cells",[]) #Get the content of extracted table

        if not cells:
            return []

        has_header = table_element.metadata.get("has_header_row",False) #check if header exists

        if has_header:
            header = cells[0] #Gets first which is  header
            rows = cells[1:] #Gets remaining rows

            chunks = self._split_rows_recursive( #Recursive split while header preserved
                table_element=table_element,
                header=header,
                rows=rows,
                section_path=routed_chunk.section_path
            )
        else:
            chunks = self._split_without_header(table_element=table_element, 
                                                cells=cells,
                                                section_path=routed_chunk.section_path)

        for index, chunk in enumerate(chunks):

            chunk.metadata["table_chunk_index"] = index #tracke child chunk index
            chunk.metadata["table_chunk_count"] = len(chunks) #total number of chunks

        return chunks

    def _fits(self, text: str) -> bool:
        return len(text) <= self.max_tokens * 4 # 4 character = 1 token

    def _build_markdown( #converts table cells to markdown
        self,
        header: list[str] | None,
        rows: list[list[str]],
    ) -> str:

        if not header:     #If no header
            return "\n".join(     # A | B
                " | ".join(row)   # C | D
                for row in rows
            )

        header_line = "| " + " | ".join(header) + " |"  #Build header same format as above

        separator = (      #| -- | -- | to  indiacte headers 
            "| "
            + " | ".join("---" for _ in header)
            + " |"
        )

        row_lines = [ #Build data rows
            "| " + " | ".join(row) + " |"
            for row in rows
        ]

        return "\n".join(   # joins entire row to form complete md file
            [header_line, separator, *row_lines]
        )

    def _split_rows_recursive(self,table_element: ExtractedElement,
                              header: list[str],
                              rows: list[list[str]],
                              section_path: list[str])->list[TableChunk]:

        text = self._build_markdown(header=header,rows=rows) #current rows to md

        if self._fits(text): #if table fits 

            return [self._create_chunk(
                table_element=table_element,
                text=text,
                cells=[header, *rows],
                section_path=section_path
            )]

        if len(rows) <=1: #if after splitting only 1 row is left in chunk
                          # so create chunk
            return [self._create_chunk(   
                table_element=table_element,
                text=text,
                cells=[header, *rows],
                section_path=section_path
            )]

        midpoint = len(rows) // 2 #Divide rows in half

        first_rows = rows[:midpoint] #first half
        second_rows = rows[midpoint:] #second half

        first_chunks = self._split_rows_recursive( #split first half recursively
            table_element=table_element,
            header=header,
            rows=first_rows,
            section_path=section_path
        )

        second_chunks = self._split_rows_recursive( #split second half recursively
            table_element=table_element,
            header=header,
            rows=second_rows,
            section_path=section_path
        )

        return first_chunks + second_chunks #add all chunks in a list 

    def _split_without_header(self,table_element:ExtractedElement,
                              cells: list[list[str]],
                              section_path: list[str])-> list[TableChunk]:

        text = self._build_markdown(header=None,rows=cells)

        if self._fits(text=text):

            return[
                self._create_chunk(
                    table_element=table_element,
                    text=text,
                    cells=cells,
                    section_path=section_path,
                )
            ]

        if len(cells) <= 1:

            return [
                self._create_chunk(
                    table_element=table_element,
                    text=text,
                    cells=cells,
                    section_path=section_path,
                )
            ]

        midpoint = len(cells) // 2

        first = self._split_without_header(
            table_element=table_element,
            cells=cells[:midpoint],
            section_path=section_path,
        )

        second = self._split_without_header(
            table_element=table_element,
            cells=cells[midpoint:],
            section_path=section_path,
        )

        return first + second

    def _create_chunk(self,table_element: ExtractedElement,
                      text:str,
                      cells:list[list[str]],
                      section_path: list[str])-> TableChunk:

        original_metadata = table_element.metadata

        metadata = {
            **original_metadata,
            "cells":cells,
            "n_rows": len(cells),
            "n_cols": max(
                (len(row) for row in cells),
                default=0,),
            "markdown": text,
            "section_path": section_path,
            "is_table_chunk":True
        }

        return TableChunk(
            text=text,
            elements=[table_element],
            metadata=metadata,
        )
            
