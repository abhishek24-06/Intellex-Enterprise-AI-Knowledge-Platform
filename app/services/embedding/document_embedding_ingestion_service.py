from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dto.final_chunk import FinalChunk
from app.models.document_chunks import DocumentChunk
from app.models.documents import Document
from app.services.embedding.bge_m3_embedding_service import BGEM3EmbeddingService
from app.services.chunk_persistence.chunk_persistence_service import ChunkPersistenceService


class DocumentEmbeddingIngestionService:
    """
    Responsibilities:

        FinalChunk[]
            ↓
        Validate document relationship
            ↓
        Verify Document exists
            ↓
        Replace existing chunks
            ↓
        Generate BGE-M3 embeddings
            ↓
        Persist DocumentChunk rows
            ↓
        Commit transaction
    """

    def __init__(self,embedding_service: BGEM3EmbeddingService):

        self.chunk_persistence_service = (
            ChunkPersistenceService(
                embedding_service=embedding_service
            )
        )

    def ingest(self,db: Session,chunks: list[FinalChunk]) -> list[DocumentChunk]:

        if not chunks:
            return []

        document_ids = {
            chunk.metadata.get("document_id")
            for chunk in chunks
        }

        if None in document_ids:
            raise ValueError("Every FinalChunk must contain 'document_id' in metadata.")

        if len(document_ids) != 1:
            raise ValueError("All FinalChunks must belong to the same document.")

        document_id = next(
            iter(document_ids)
        )

        if not isinstance(document_id,int,):
            raise ValueError("FinalChunk metadata document_id must be an integer.")

        document = db.execute(
            select(Document).where(Document.document_id == document_id)).scalar_one_or_none()

        if document is None:
            raise ValueError(f"Document {document_id} does not exist.")

        for index, chunk in enumerate(
            chunks
        ):

            if not isinstance(chunk,FinalChunk,):
                raise ValueError(f"Invalid FinalChunk at index {index}.")

            if not chunk.text or not chunk.text.strip():
                raise ValueError(f"FinalChunk at index {index} has empty text.")

            if chunk.metadata.get("document_id") != document_id:
                raise ValueError(f"FinalChunk at index {index} belongs to a different document.")

            if not isinstance(chunk.section_path,list):
                raise ValueError(f"FinalChunk at index{index} has invalid section_path.")

        db.query(
            DocumentChunk
        ).filter(
            DocumentChunk.document_id
            == document_id
        ).delete(
            synchronize_session=False
        )

        db.flush()

        try:
            persisted_chunks = (self.chunk_persistence_service.persist(db=db,chunks=chunks))

            if len(persisted_chunks) != len(chunks):
                raise RuntimeError("Persisted chunk count does not match input chunk count.")

            db.commit()

            return persisted_chunks

        except Exception:

            db.rollback()

            raise