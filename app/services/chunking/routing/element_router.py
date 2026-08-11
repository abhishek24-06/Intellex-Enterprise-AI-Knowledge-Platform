from app.dto.chunk_candidate import ChunkCandidate
from app.dto.routed_chunk import RoutedChunk
from app.enums.chunk_type import ChunkType
from app.enums.element_type import ElementType

class ElementRouter:

    DELEGATED_TYPES = {
        ElementType.TABLE,
        ElementType.CODE_BLOCK
    }

    def route(self, candidate: ChunkCandidate)->list[RoutedChunk]:

        routed_chunks: list[RoutedChunk] = []

        narrative_elements = [element
                              for element in candidate.elements
                              if element.element_type not in self.DELEGATED_TYPES
                            ]

        delegated_elements = [element
                              for element in candidate.elements
                              if element.element_type in self.DELEGATED_TYPES]

        #Narrative - paras...
        if candidate.text.strip() and narrative_elements:

            first_narrative = min(narrative_elements,
                                  key=lambda element: element.order_index)

            routed_chunks.append(
                RoutedChunk(
                    chunk_type=ChunkType.NARRATIVE,
                    elements=narrative_elements,
                    text=candidate.text,
                    section_path=candidate.section_path,
                    order_index=first_narrative.order_index
                ))

        #Table and Code
        for element in delegated_elements:

            chunk_type = self._get_chunk_type(
                element.element_type
            )

            routed_chunks.append(
                RoutedChunk(
                    chunk_type=chunk_type,
                    elements=[element],
                    text=
                    None,
                    section_path=candidate.section_path,
                    order_index=element.order_index
                )
            )
        return routed_chunks

    def _get_chunk_type(self,element_type:ElementType)->ChunkType:

        if element_type == ElementType.TABLE:
            return ChunkType.TABLE

        if element_type == ElementType.CODE_BLOCK:
            return ChunkType.CODE

        raise ValueError(
            f"Unsupported delegated element type: {element_type}"
        ) 
        