from functools import lru_cache

from app.services.chunking.code.code_chunker import CodeChunker
from app.services.chunking.final_chunker_validator.validator import FinalChunkValidator
from app.services.chunking.hierarchy.hierarchy_chunker import HierarchyChunker
from app.services.generation.openrouter_client import OpenRouterClient
from app.services.chunking.llm_chunker.semantic_chunker import SemanticChunker
from app.services.chunking.recursive_splitter.narrative_safety_splitter import NarrativeSafetySplitter
from app.services.chunking.routing.element_router import ElementRouter
from app.services.chunking.structure_builder.structure_builder import DocumentStructureBuilder
from app.services.chunking.structure_detection.detector import StructureDetector
from app.services.chunking.table.table_chunker import TableChunker
from app.services.cleaning.element_cleaner import ElementCleaner
from app.services.extraction.extraction_factory import ExtractorFactory
from app.services.ingestion.metadata.chunk_attacher import ChunkContextAttacher
from app.services.ingestion.metadata.metadata_enricher import MetadataEnricher
from app.services.pipeline.document_chunker_pipeline import DocumentChunker
from app.services.pipeline.document_ingestion_pipeline import DocumentIngestionPipeline
from app.services.embedding.bge_m3_embedding_service import BGEM3EmbeddingService
from app.services.embedding.document_embedding_ingestion_service import DocumentEmbeddingIngestionService
from app.services.document_processing_service import DocumentProcessingService

def build_document_chunker():

    structure_detector = StructureDetector()

    structure_builder = DocumentStructureBuilder()

    hierarchy_chunker = HierarchyChunker()

    openrouter_client = OpenRouterClient()
    semantic_chunker = SemanticChunker(llm_client=openrouter_client)

    element_router = ElementRouter()

    narrative_safety_splitter = NarrativeSafetySplitter(max_tokens=1000)

    table_chunker = TableChunker(max_tokens=1000)

    code_chunker = CodeChunker(max_tokens=1000)

    final_chunk_validator = FinalChunkValidator()

    return DocumentChunker(
        structure_detector=structure_detector,
        structure_builder=structure_builder,
        hierarchy_chunker=hierarchy_chunker,
        semantic_chunker=semantic_chunker,
        element_router=element_router,
        narrative_safety_splitter=narrative_safety_splitter,
        table_chunker=table_chunker,
        code_chunker=code_chunker,
        final_chunk_validator=final_chunk_validator,
    )

def build_document_ingestion_pipeline() -> DocumentIngestionPipeline:

    extractor_factory = ExtractorFactory()

    element_cleaner = ElementCleaner()

    document_chunker = build_document_chunker()

    metadata_enricher = MetadataEnricher()

    context_attacher = ChunkContextAttacher()

    return DocumentIngestionPipeline(
        extractor_factory=extractor_factory,
        element_cleaner=element_cleaner,
        document_chunker=document_chunker,
        metadata_enricher=metadata_enricher,
        context_attacher=context_attacher,
    )

@lru_cache(maxsize=1)
def build_embedding_ingestion_service():

    embedding_service = BGEM3EmbeddingService()

    return DocumentEmbeddingIngestionService(
        embedding_service=embedding_service
    )

def build_document_processing_service():
    """
    Combines:
        extraction/chunking
                +
        embedding/pgvector persistence
    """
    ingestion_pipeline = (build_document_ingestion_pipeline())

    embedding_ingestion_service = (build_embedding_ingestion_service())

    return DocumentProcessingService(
        ingestion_pipeline=ingestion_pipeline,
        embedding_ingestion_service=(embedding_ingestion_service),
    )