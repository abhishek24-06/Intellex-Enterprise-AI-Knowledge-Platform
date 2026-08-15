from app.dto.chunk_context import ChunkContext
from app.dto.extraction_result import ExtractionResult
from app.dto.final_chunk import FinalChunk
from app.services.chunking.final_chunker.document_chunker import DocumentChunker
from app.services.ingestion.metadata.chunk_attacher import ChunkContextAttacher
from app.services.ingestion.metadata.metadata_enricher import MetadataEnricher


class DocumentIngestionPipeline:

    def __init__(self,
                 document_chunker:DocumentChunker,
                 metadata_enricher:MetadataEnricher,
                 context_attacher:ChunkContextAttacher):

        self.document_chunker = document_chunker
        self.metadata_enricher = metadata_enricher
        self.context_attacher = context_attacher

    def process(self,extraction_result:ExtractionResult,context:ChunkContext)->list[FinalChunk]:

        chunks = self.document_chunker.chunk(extraction_result)

        chunks = self.metadata_enricher.enrich(chunks)

        chunks = self.context_attacher.attach(chunks,context)

        return chunks