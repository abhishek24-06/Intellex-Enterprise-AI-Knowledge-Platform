from sqlalchemy.orm import Session

from app.models.documents import Document, DocumentStatus
from app.services.pipeline.document_ingestion_pipeline import DocumentIngestionPipeline
from app.services.embedding.document_embedding_ingestion_service import DocumentEmbeddingIngestionService

class DocumentProcessingService:

    def __init__(self,ingestion_pipeline:DocumentIngestionPipeline,embedding_ingestion_service:DocumentEmbeddingIngestionService):

        self.ingestion_pipeline = ingestion_pipeline
        self.embedding_ingestion_service = embedding_ingestion_service

    def process(self,db:Session,document:Document):

        if document is None:
            raise ValueError("Document cannot be None")

    #PROCESSING

        document.status = (DocumentStatus.PROCESSING)
        document.processing_error = None

        db.add(document)
        db.commit()
        db.refresh(document)

        try:
        #Complete Ingestion Pipeline

            final_chunks = (self.ingestion_pipeline.ingest(document))

            self.embedding_ingestion_service.ingest(db=db,chunks=final_chunks)            

        #IF SUCCESS
             
            document.status = (DocumentStatus.READY)
            document.processing_error = None
    
            db.add(document)
            db.commit()
            db.refresh(document)

            return final_chunks

        except Exception as exc:

        #FAILURE

            document.status = (DocumentStatus.FAILED)
            document.processing_error = (str(exc)[:500])
    
            db.add(document)
            db.commit()
            db.refresh(document)

            raise

            

