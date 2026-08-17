from sqlalchemy.orm import Session

from app.dto.final_chunk import FinalChunk
from app.models.document_chunks import DocumentChunk
from app.services.embedding.bge_m3_embedding_service import BGEM3EmbeddingService


class ChunkPersistenceService:

    def __init__(self,embedding_service: BGEM3EmbeddingService):

        self.embedding_service = embedding_service

    def persist(self,db: Session,chunks: list[FinalChunk]) -> list[DocumentChunk]:

        if not chunks:
            return []

        texts = [chunk.text for chunk in chunks]

        # Generate all embeddings in one batch.
        embeddings = self.embedding_service.embed_texts(texts)

        if len(embeddings) != len(chunks):
            raise ValueError(
                "Embedding count does not match chunk count."
            )

        document_chunks: list[DocumentChunk] = []

        for chunk_index, (chunk, embedding) in enumerate(
            zip(chunks, embeddings)
        ):
            token_count = self.embedding_service.count_tokens(
                chunk.text
            )
            if "document_id" not in chunk.metadata:
                raise ValueError("FinalChunk metadata must contain document_id.")

            document_id = chunk.metadata["document_id"]

            document_chunk = DocumentChunk(
                document_id=document_id,
                chunk_index=chunk_index,
                chunk_text=chunk.text,
                token_count=token_count,
                embedding=embedding,
                metadata_json=self._build_metadata(chunk),
            )

            document_chunks.append(document_chunk)

        db.add_all(document_chunks)
        db.flush()

        return document_chunks

    @staticmethod
    def _build_metadata(
        chunk: FinalChunk,
    ) -> dict:

        metadata = dict(chunk.metadata)

        metadata["chunk_type"] = chunk.chunk_type.value
        metadata["section_path"] = list(chunk.section_path)
        metadata["order_index"] = chunk.order_index

        return metadata