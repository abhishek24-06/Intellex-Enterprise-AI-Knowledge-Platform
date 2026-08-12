import logging

from app.dto.chunk_candidate import ChunkCandidate
from app.dto.extraction_result import ExtractionResult
from app.enums.element_type import ElementType
from app.services.chunking.llm_chunker.gemini_client import GeminiClient

logger = logging.getLogger(__name__)

class SemanticChunker:

    DELEGATED_TYPES = {ElementType.TABLE,
                       ElementType.CODE_BLOCK}

    def __init__(self,llm_client:GeminiClient):
        self.llm_client = llm_client

    def chunk(self,extraction_result:ExtractionResult)->list[ChunkCandidate]:

        elements = sorted(extraction_result.elements,key=lambda element: element.order_index) #Sort elements in original order

        if not elements:
            return []
        
        narrative_elements = [element  #Keeps only para, list
                            for element in elements
                            if (
                                element.element_type not in self.DELEGATED_TYPES
                                and element.text.strip()
                            )]

        if not narrative_elements:
            return [
                ChunkCandidate(
                    text="",
                    elements=elements,
                    heading=None,
                    section_path=[],
                )
            ]

        try:
            prompt = self._build_prompt(narrative_elements)
    
            response = self.llm_client.detect_boundaries(prompt)
    
            boundaries = self._validate_boundaries(boundaries=response.boundaries,
                                                   narrative_elements=narrative_elements)
    
            return self._build_candidates(elements=elements,
                                        boundaries=boundaries)

        except Exception as exc:
            logger.exception(
                "Semantic boundary detection failed; "
                "falling back to deterministic chunking",

            )
            return self._fallback(elements=elements)
        
    def _build_prompt(self, elements) -> str:

        content = "\n\n".join(
            f"[{element.order_index}] {element.text.strip()}"
            for element in elements
        )
    
        return f"""
        You are a semantic document boundary detector.
        
        Your task is to identify where a new semantic topic begins.
        
        Do NOT rewrite, summarize, classify, or modify the content.
        
        Return only the starting order_index of each semantic group.
        
        Rules:
        - The first boundary must be the first provided order_index.
        - Every boundary must correspond to one of the provided order_index values.
        - Boundaries must be sorted.
        - Use semantic topic changes, not arbitrary paragraph boundaries.
        - Do not create a boundary merely because formatting changes.
        - Related paragraphs should remain together.
        
        Document elements:
        
        {content}
        """

    def _validate_boundaries(self,boundaries: list[int],narrative_elements) -> list[int]:

        valid_indexes = {element.order_index
                        for element in narrative_elements
        }
    
        if not boundaries:
            raise ValueError("Gemini returned no semantic boundaries.")
    
        if any(boundary not in valid_indexes
              for boundary in boundaries
        ):
            raise ValueError("Gemini returned an invalid boundary.")
    
        if boundaries != sorted(set(boundaries)):
            raise ValueError("Gemini boundaries must be sorted and unique.")
    
        if boundaries[0] != narrative_elements[0].order_index:
            raise ValueError("First boundary must be the first narrative element.")
    
        return boundaries

    def _build_candidates(self,elements,boundaries)-> list[ChunkCandidate]:

        candidates = []

        for index,boundary  in enumerate(boundaries):

            start = boundary

            end =(
                boundaries[index + 1]
                if index + 1 < len(boundaries)
                else None
            )

            group = [element
                     for element in elements
                     if element.order_index >= start
                     and (
                         end is None
                         or element.order_index < end
                     )]

            if not group:
                continue

            narrative = [element
                         for element in group
                         if(
                             element.element_type not in self.DELEGATED_TYPES
                             and element.text.strip()
                         )]

            if not narrative:
                continue

            candidates.append(
                ChunkCandidate(
                    text=self._build_text(narrative),
                    elements=group,
                    heading=None,
                    section_path=[]
                )
            )

        return candidates

    def _build_text(self, narrative_elements) -> str:
    
        return "\n\n".join(
            element.text.strip()
            for element in narrative_elements
            if element.text.strip()
        )

    FALLBACK_MAX_CHARS = 2000
    
    def _fallback(self, elements) -> list[ChunkCandidate]:
        candidates: list[ChunkCandidate] = []
    
        current_group = []
        current_len = 0
    
        for element in elements:
    
            # Tables/code don't contribute to narrative size,
            # but remain attached to the current group.
            if element.element_type in self.DELEGATED_TYPES:
                current_group.append(element)
                continue
    
            if not element.text.strip():
                continue
    
            projected_len = current_len + len(element.text)
    
            if (
                current_group
                and current_len > 0
                and projected_len > self.FALLBACK_MAX_CHARS
            ):
                candidates.append(
                    self._build_fallback_candidate(current_group)
                )
    
                current_group = []
                current_len = 0
    
            current_group.append(element)
            current_len += len(element.text)
    
        if current_group:
            candidates.append(
                self._build_fallback_candidate(current_group)
            )
    
        return candidates

    def _build_fallback_candidate(self, group) -> ChunkCandidate:

        narrative = [element
            for element in group
            if (
                element.element_type not in self.DELEGATED_TYPES
                and element.text.strip()
            )
        ]
    
        return ChunkCandidate(
            text=self._build_text(narrative),
            elements=group,
            heading=None,
            section_path=[],
        )