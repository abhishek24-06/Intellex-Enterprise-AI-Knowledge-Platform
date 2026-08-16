from sqlalchemy.orm import Session

from app.models.documents import Document, DocumentStatus
from app.services.pipeline.document_ingestion_pipeline import DocumentIngestionPipeline

class DocumentProcessingService:

    def __init__(self,ingestion_pipeline:DocumentIngestionPipeline):

        self.ingestion_pipeline = ingestion_pipeline

    def process(self,db:Session,document:Document):

        if document is None:
            raise ValueError("Document cannot be None")

    #PROCESSING

        document.processing_error = None

        db.add(document)
        db.commit()
        db.refresh(document)

        try:
        #Complete Ingestion Pipeline

            final_chunks = (self.ingestion_pipeline.ingest(document))

            output_path = "debug_pdf_chunks.txt"

            with open(output_path, "w", encoding="utf-8") as f:

                f.write("\n" + "=" * 80 + "\n")
                f.write("FINAL CHUNKS\n")
                f.write("=" * 80 + "\n")
            
                f.write(f"Document ID : {document.document_id}\n")
                f.write(f"Total chunks: {len(final_chunks)}\n")
            
                for i, chunk in enumerate(final_chunks):

                    f.write("\n" + "-" * 80 + "\n")
                    f.write(f"CHUNK {i}\n")
                    f.write("-" * 80 + "\n")
            
                    f.write(f"chunk_type   : {chunk.chunk_type}\n")
                    f.write(f"order_index  : {chunk.order_index}\n")
                    f.write(f"section_path : {chunk.section_path}\n")
            
                    f.write("\nTEXT:\n")
                    f.write(chunk.text or "")
                    f.write("\n")
            
                    f.write("\nMETADATA:\n")
                    f.write(str(chunk.metadata))
                    f.write("\n")

                f.write("\n" + "=" * 80 + "\n")
            print(f"Debug chunks written to: {output_path}")

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

            

