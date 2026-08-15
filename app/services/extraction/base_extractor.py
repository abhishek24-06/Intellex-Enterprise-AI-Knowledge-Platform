from abc import ABC, abstractmethod

from app.dto.extraction_result import ExtractionResult

class BaseExtractor(ABC):

    @abstractmethod
    def extract(self,file_path:str,
                document_id:str |None=None,filename:str |None=None)->ExtractionResult:
        """Extract structured elements from a document."""
        pass

    def _base_metadata(self,document_id:str|None, filename:str|None)->dict:

        return{
            "document_id":document_id,
            "filename": filename
        }

    def _table_to_markdown(self,rows_data:list[list[str]],has_header_row:bool)->str: #Convert table in 2D into Markdown table format

        if not rows_data:
            return ""

        markdown = []

        if has_header_row:
            markdown.append(
                "| " + " | ".join(rows_data[0]) + " |" 
            )
    
            markdown.append(
                "| " + " | ".join("---" for _ in rows_data[0]) + " |" #Tells everything above  is header
            )
    
            start = 1 #Skips header row this avoids duplicates

        else:  #NO header
            start = 0

        for row in rows_data[start:]:
            markdown.append(
                "| " + " | ".join(row) + " |"
            )
        return "\n".join(markdown)