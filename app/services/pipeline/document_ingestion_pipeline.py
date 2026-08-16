from app.dto.chunk_context import ChunkContext
from app.dto.final_chunk import FinalChunk
from app.dto.extraction_result import ExtractionResult

from app.models.documents import Document
from app.services.extraction.extraction_factory import (ExtractorFactory)
from app.services.cleaning.element_cleaner import (ElementCleaner)
from app.services.pipeline.document_chunker_pipeline import (DocumentChunker)
from app.services.ingestion.metadata.metadata_enricher import (MetadataEnricher)
from app.services.ingestion.metadata.chunk_attacher import (ChunkContextAttacher)

class DocumentIngestionPipeline:
    """
    Coordinates the complete document ingestion pipeline.

        Document
            ↓
        ExtractorFactory
            ↓
        Extractor
            ↓
        ExtractionResult
            ↓
        ElementCleaner
            ↓
        DocumentChunker
            ↓
        MetadataEnricher
            ↓
        ChunkContextAttacher
            ↓
        list[FinalChunk]

    """

    def __init__(self,
        extractor_factory: ExtractorFactory,
        element_cleaner: ElementCleaner,
        document_chunker: DocumentChunker,
        metadata_enricher: MetadataEnricher,
        context_attacher: ChunkContextAttacher,
    ):
        self.extractor_factory = extractor_factory
        self.element_cleaner = element_cleaner
        self.document_chunker = document_chunker
        self.metadata_enricher = metadata_enricher
        self.context_attacher = context_attacher

    def ingest(self,document: Document)->list[FinalChunk]:
        """
        Process one Document through thecomplete ingestion pipeline.

        Parameters:
        document:
            Persisted Document containing the validated file
            path, MIME type, document identity and upload context.

        Returns:
        list[FinalChunk]
            Validated and context-enriched chunks ready for
            the next ingestion phase.
        """

        self._validate_document(document)

    #EXTRACTOR SELECTION

        extractor = (self.extractor_factory.get_extractor(document.mime_type))

    #EXTRACTION

        extraction_result = (
            extractor.extract(
                file_path=document.file_path,
                document_id=document.document_id,
                filename=document.original_filename,
            )
        )

        if not isinstance(extraction_result,ExtractionResult):

            raise TypeError("Extractor must return an ExtractionResult.")

    #ELEMENT CLEANING

        cleaned_result = (
            self.element_cleaner.clean(
                extraction_result
            )
        )

        if not isinstance(cleaned_result,ExtractionResult):

            raise TypeError("ElementCleaner must return an ExtractionResult.")

    #CHUNKING

        chunks = (
            self.document_chunker.chunk(
                cleaned_result
            )
        )

    #METADATA ENRICHMENT

        chunks = (
            self.metadata_enricher.enrich(
                chunks
            )
        )
    #DOCUMENT CONTEXT

        context = self._build_chunk_context(
            document
        )

    #ATTACH UPLOAD-TIME CONTEXT

        chunks = (
            self.context_attacher.attach(
                chunks,
                context,
            )
        )

        return chunks

    # DOCUMENT VALIDATION

    @staticmethod
    def _validate_document(
        document: Document,
    ) -> None:
        """
        Validate that the pipeline received a usable
        persisted Document.
        """

        if document is None:
            raise ValueError(
                "Document cannot be None."
            )

        if not document.document_id:
            raise ValueError(
                "Document must have a document_id."
            )

        if not document.file_path:
            raise ValueError(
                "Document must have a file_path."
            )

        if not document.original_filename:
            raise ValueError(
                "Document must have an original_filename."
            )

        if not document.mime_type:
            raise ValueError(
                "Document must have a mime_type."
            )

        if document.organization_id is None:
            raise ValueError(
                "Document must have an organization_id."
            )

        if document.uploaded_by is None:
            raise ValueError(
                "Document must have an uploaded_by value."
            )

        if document.visibility is None:
            raise ValueError(
                "Document must have a visibility value."
            )

        if document.version is None:
            raise ValueError(
                "Document must have a version."
            )

    # CHUNK CONTEXT

    @staticmethod
    def _build_chunk_context(
        document: Document,
    ) -> ChunkContext:
        """
        Convert authoritative Document-level context into the
        immutable ChunkContext consumed by ChunkContextAttacher.
        """

        return ChunkContext(
            document_id=document.document_id,
            organization_id=document.organization_id,
            uploaded_by=document.uploaded_by,
            visibility=document.visibility,
            document_version=document.version,
        )