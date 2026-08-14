from app.dto.chunk_candidate import ChunkCandidate
from app.dto.extraction_result import ExtractionResult
from app.dto.routed_chunk import RoutedChunk
from app.dto.final_chunk import FinalChunk

from app.enums.chunk_type import ChunkType
from app.enums.element_type import ElementType
from app.services.chunking.structure_detection.models import StructureType

from app.services.chunking.structure_detection.detector import StructureDetector
from app.services.chunking.structure_builder.structure_builder import DocumentStructureBuilder
from app.services.chunking.hierarchy.hierarchy_chunker import HierarchyChunker
from app.services.chunking.llm_chunker.semantic_chunker import SemanticChunker

from app.services.chunking.routing.element_router import ElementRouter
from app.services.chunking.recursive_splitter.narrative_safety_splitter import NarrativeSafetySplitter

from app.services.chunking.table.table_chunker import TableChunker
from app.services.chunking.code.code_chunker import CodeChunker

class DocumentChunker:

    DELEGATED_TYPES = {
        ElementType.TABLE,
        ElementType.CODE_BLOCK
    }

    def __init__(
        self,
        structure_detector: StructureDetector,
        structure_builder: DocumentStructureBuilder,
        hierarchy_chunker: HierarchyChunker,
        semantic_chunker: SemanticChunker,
        element_router: ElementRouter,
        narrative_safety_splitter: NarrativeSafetySplitter,
        table_chunker: TableChunker,
        code_chunker: CodeChunker
    ): 

        self.structure_detector = structure_detector
        self.structure_builder = structure_builder
        self.hierarchy_chunker = hierarchy_chunker
        self.semantic_chunker = semantic_chunker
        self.element_router = element_router
        self.narrative_safety_splitter = narrative_safety_splitter
        self.table_chunker = table_chunker
        self.code_chunker = code_chunker

    def chunk(self,extraction_result: ExtractionResult) -> list[FinalChunk]:

        if not extraction_result.elements:
            return []

        detection = self.structure_detector.detect(extraction_result)

        candidates = self._build_candidates(
            extraction_result=extraction_result,
            structure_type=detection.structure_type
        ) 

        routed_chunks: list[RoutedChunk] = []

        for candidate in candidates:
            routed_chunks.extend(self.element_router.route(candidate))

        final_chunks: list[FinalChunk] = []

        for routed_chunk in routed_chunks:
            final_chunks.extend(self._process_routed_chunk(routed_chunk))

        final_chunks.sort(key=lambda chunk: chunk.order_index)

        return final_chunks

    def _build_candidates(self,extraction_result: ExtractionResult,structure_type:StructureType)-> list[ChunkCandidate]:

        if structure_type == StructureType.STRUCTURED:
            tree = self.structure_builder.build(extraction_result)

            return self.hierarchy_chunker.chunk(tree)

        if structure_type == StructureType.UNSTRUCTURED:
            return self.semantic_chunker.chunk(extraction_result)

        if structure_type == StructureType.TABULAR:
            return self._build_tabular_candidates(extraction_result)

        raise ValueError(f"Unsupported structure type: {structure_type}")

    def _build_tabular_candidates(self,extraction_result:ExtractionResult)->list[ChunkCandidate]:

        elements = sorted(extraction_result.elements,
                          key=lambda element: element.order_index)

        narrative_elements = [element
                              for element in elements
                              if(
                                  element.element_type not in self.DELEGATED_TYPES
                                  and element.text 
                                  and element.text.strip()
                              )]

        text = "\n\n".join(element.text.strip()
                           for element in narrative_elements)

        return [
            ChunkCandidate(
                text=text,
                elements=elements,
                heading=None,
                section_path=[]
            )
        ]

    def _process_routed_chunk(self,routed_chunk: RoutedChunk)->list[FinalChunk]:

        if routed_chunk.chunk_type == ChunkType.NARRATIVE:
            return self._process_narrative(routed_chunk)

        if routed_chunk.chunk_type == ChunkType.TABLE:
            return self._process_table(routed_chunk)

        if routed_chunk.chunk_type == ChunkType.CODE:
            return self._process_code(routed_chunk)

        raise ValueError(f"Unsupported chunk type: {routed_chunk.chunk_type}")

    def _process_narrative(self,routed_chunk: RoutedChunk)->list[FinalChunk]:

        chunks = self.narrative_safety_splitter.split(routed_chunk)

        return[self._finalize_narrative_chunk(chunk)
               for chunk in chunks
            ]

    def _finalize_narrative_chunk(self,chunk:RoutedChunk)->FinalChunk:

        return FinalChunk(text=chunk.text or "",
                          elements=chunk.elements,
                          chunk_type=ChunkType.NARRATIVE,
                          section_path=chunk.section_path,
                          order_index=chunk.order_index,
                          metadata={})
    
    def _process_table(self,routed_chunk:RoutedChunk)->list[FinalChunk]:

        table_chunks = self.table_chunker.chunk(routed_chunk)

        return [
            self._finalize_specialized_chunk(
                source=routed_chunk,
                chunk=table_chunk,
                chunk_type=ChunkType.TABLE
            )
            for table_chunk in table_chunks
        ]

    def _process_code(self,routed_chunk:RoutedChunk)->list[FinalChunk]:

        code_chunks = self.code_chunker.chunk(routed_chunk)

        return [
            self._finalize_specialized_chunk(
                source=routed_chunk,
                chunk=code_chunk,
                chunk_type=ChunkType.CODE
            )
            for code_chunk in code_chunks
        ]

    def _finalize_specialized_chunk(self,
                                    source:RoutedChunk,
                                    chunk,
                                    chunk_type:ChunkType)->FinalChunk:

        return FinalChunk(
            text=chunk.text,
            elements=chunk.elements,
            chunk_type=chunk_type,
            section_path=source.section_path,
            order_index=source.order_index,
            metadata=dict(chunk.metadata)
        )