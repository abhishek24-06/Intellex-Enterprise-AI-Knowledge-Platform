import re

from app.dto.code_chunk import CodeChunk
from app.dto.extracted_element import ExtractedElement
from app.dto.routed_chunk import RoutedChunk

class CodeChunker:

    STRUCTURAL_MARKERS = {
    "python": (
        r"^[ \t]*class ",
        r"^[ \t]*(?:async )?def ",
    ),
    "javascript": (
        r"^[ \t]*class ",
        r"^[ \t]*function ",
        r"^[ \t]*export function ",
    ),
    "typescript": (
        r"^[ \t]*class ",
        r"^[ \t]*function ",
        r"^[ \t]*export function ",
    ),
    "java": (
        r"^[ \t]*class ",
        r"^[ \t]*(?:public|private|protected) ",
    ),
}

    def __init__(self,max_tokens:int = 1000):

        self.max_tokens = max_tokens

    def chunk(self,routed_chunk:RoutedChunk)->list[CodeChunk]:

        if not routed_chunk.elements:
            return []

        code_element = routed_chunk.elements[0]

        if not code_element.text.strip(): #removes whitespaces if empty return null
            return []

        language = code_element.metadata.get("language") #Gets language type

        return self._split_code_recursive(code_element=code_element,
                                          code=code_element.text,
                                          language=language,
                                          section_path=routed_chunk.section_path)

    def _fits(self,code:str)->bool:
        return len(code) <= self.max_tokens * 4

    def _create_chunk(self,code_element:ExtractedElement,text:str,language:str | None,section_path:list[str])->CodeChunk:

        metadata = {
            **code_element.metadata,
            "language": language,
            "section_path": section_path
        }        

        return CodeChunk(
            text=text,
            elements=[code_element],
            metadata=metadata,
        )

    def _split_code_recursive(self,code_element:ExtractedElement,code:str,language:str | None,section_path: list[str])->list[CodeChunk]:

        if self._fits(code):
            return[self._create_chunk(
                code_element=code_element,
                text=code,
                language=language,
                section_path=section_path
            )]    

        parts = self._split_structurally(code=code,language=language)

        if len(parts) <= 1:
            parts = self._split_lines_raw(code)

        if len(parts) <= 1:
            return[
                self._create_chunk(
                    code_element=code_element,
                    text=code,
                    language=language,
                    section_path=section_path
                )
            ]

        chunks: list[CodeChunk] = []

        for part in parts:
            chunks.extend(
                self._split_code_recursive(
                    code_element=code_element,
                    code=part,
                    language=language,
                    section_path=section_path,
            )
        )

        return chunks

    def _split_lines_raw(self,code: str,max_lines: int = 40)->list[str]:
    
        lines = code.splitlines()
    
        return [
            "\n".join(lines[i:i + max_lines])
            for i in range(0, len(lines), max_lines)
        ]

    def _split_structurally(self,code:str,language:str | None)-> list[str]:

        if not language:
            return self._split_lines_raw(code)

        markers = self.STRUCTURAL_MARKERS.get(language.lower())

        if not markers:
            return self._split_lines_raw(code)

        return self._split_by_markers(code=code,markers=markers)

    def _split_by_markers(self,code: str,markers: tuple[str, ...],) -> list[str]:

        positions: list[int] = []
    
        for marker in markers:
            pattern = re.compile(marker, re.MULTILINE)
    
            for match in pattern.finditer(code):
                positions.append(match.start())
    
        if not positions:
            return self._split_lines_raw(code)
    
        positions = sorted(set(positions))
    
        parts: list[str] = []
    
        first = positions[0]
    
        if first > 0:
            parts.append(code[:first])
    
        for i, position in enumerate(positions):
            end = (
                positions[i + 1]
                if i + 1 < len(positions)
                else len(code)
            ) 
            parts.append(code[position:end])
    
        return [part for part in parts if part]