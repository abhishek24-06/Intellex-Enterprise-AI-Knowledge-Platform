from sqlalchemy import select
from sqlalchemy.orm import Session

from app.dto.final_chunk import FinalChunk
from app.models.document_chunks import DocumentChunk
from app.models.documents import Document, EmbeddingStatus
from app.services.embedding.bge_m3_embedding_service import (
    BGEM3EmbeddingService,
)
from app.services.chunk_persistence.chunk_persistence_service import (
    ChunkPersistenceService,
)


class DocumentEmbeddingIngestionService:
    """
    Connects the final chunking pipeline to the embedding pipeline.

    Flow:

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
        Update document embedding metadata
            ↓
        Commit
    """

    def __init__(
        self,
        embedding_service: BGEM3EmbeddingService,
    ):
        self.embedding_service = embedding_service

        self.chunk_persistence_service = (
            ChunkPersistenceService(
                embedding_service=embedding_service
            )
        )

    def ingest(
        self,
        db: Session,
        chunks: list[FinalChunk],
    ) -> list[DocumentChunk]:

        # --------------------------------------------------------------
        # Empty input
        # --------------------------------------------------------------

        if not chunks:
            return []

        # --------------------------------------------------------------
        # Validate document IDs
        # --------------------------------------------------------------

        document_ids = {
            chunk.metadata.get("document_id")
            for chunk in chunks
        }

        if None in document_ids:
            raise ValueError(
                "Every FinalChunk must contain "
                "'document_id' in metadata."
            )

        if len(document_ids) != 1:
            raise ValueError(
                "All FinalChunks must belong "
                "to the same document."
            )

        document_id = next(iter(document_ids))

        if not isinstance(document_id, int):
            raise ValueError(
                "FinalChunk metadata document_id "
                "must be an integer."
            )

        # --------------------------------------------------------------
        # Verify document exists
        # --------------------------------------------------------------

        document = db.execute(
            select(Document).where(
                Document.document_id == document_id
            )
        ).scalar_one_or_none()

        if document is None:
            raise ValueError(
                f"Document {document_id} does not exist."
            )

        try:

            # ----------------------------------------------------------
            # Mark embedding as processing
            # ----------------------------------------------------------

            document.embedding_status = EmbeddingStatus.PROCESSING
            document.embedding_model = (
                BGEM3EmbeddingService.MODEL_NAME
            )

            db.add(document)

            # ----------------------------------------------------------
            # Validate chunks
            # ----------------------------------------------------------

            for index, chunk in enumerate(chunks):

                if not isinstance(chunk, FinalChunk):
                    raise ValueError(
                        f"Invalid FinalChunk at index {index}."
                    )

                if not chunk.text or not chunk.text.strip():
                    raise ValueError(
                        f"FinalChunk at index {index} "
                        "has empty text."
                    )

                if (
                    chunk.metadata.get("document_id")
                    != document_id
                ):
                    raise ValueError(
                        f"FinalChunk at index {index} "
                        "belongs to a different document."
                    )

                if not isinstance(
                    chunk.section_path,
                    list,
                ):
                    raise ValueError(
                        f"FinalChunk at index {index} "
                        "has invalid section_path."
                    )

            # ----------------------------------------------------------
            # Remove previous chunks
            # ----------------------------------------------------------

            db.query(
                DocumentChunk
            ).filter(
                DocumentChunk.document_id
                == document_id
            ).delete(
                synchronize_session=False
            )

            db.flush()

            # ----------------------------------------------------------
            # Generate embeddings + persist chunks
            # ----------------------------------------------------------

            persisted_chunks = (
                self.chunk_persistence_service.persist(
                    db=db,
                    chunks=chunks,
                )
            )

            # ----------------------------------------------------------
            # Validate persistence
            # ----------------------------------------------------------

            if len(persisted_chunks) != len(chunks):
                raise RuntimeError(
                    "Persisted chunk count does not "
                    "match input chunk count."
                )

            # ----------------------------------------------------------
            # Mark embedding as ready
            # ----------------------------------------------------------

            document.embedding_model = (
                BGEM3EmbeddingService.MODEL_NAME
            )

            document.embedding_status = EmbeddingStatus.COMPLETED

            db.add(document)

            # ----------------------------------------------------------
            # Commit everything
            # ----------------------------------------------------------

            db.commit()

            return persisted_chunks

        except Exception:

            # ----------------------------------------------------------
            # Rollback chunk changes
            # ----------------------------------------------------------

            db.rollback()

            # ----------------------------------------------------------
            # Mark embedding as failed
            # ----------------------------------------------------------

            try:

                document.embedding_status = EmbeddingStatus.FAILED

                db.add(document)
                db.commit()

            except Exception:

                db.rollback()

            raise