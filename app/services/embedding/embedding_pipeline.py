from typing import List

from sqlalchemy.orm import Session

from app.dto.final_chunk import FinalChunk
from app.models.document_chunks import DocumentChunk
from app.services.embedding.bge_m3_embedding_service import BGEM3EmbeddingService

class EmbeddingPipeline:

    EMBEDDING_DIMENSION = 1024

    def __init__(self,embedding_service:BGEM3EmbeddingService):

        self.embedding_service = embedding_service

    def process(self,db:Session,chunks:List[FinalChunk])->List[DocumentChunk]:

        if not chunks:
            return []

        texts = [chunk.text
                 for chunk in chunks]

        embeddings = self.embedding_service.embed_texts(texts=texts)

        if len(embeddings) !=  len(chunks):
            raise ValueError(
                "Embedding count does not match chunk count. "
                f"chunks={len(chunks)}, "
                f"embeddings={len(embeddings)}"
            )

        for index, embedding in enumerate(embeddings):

            if len(embedding) != self.EMBEDDING_DIMENSION:
                raise ValueError(
                    "Invalid embedding dimension for chunk "
                    f"{index}. "
                    f"Expected {self.EMBEDDING_DIMENSION}, "
                    f"got {len(embedding)}."
                )

        document_chunks = []

        for chunk_index, (chunk,embedding) in enumerate(zip(chunks,embeddings)):

            token_count = (
                self.embedding_service.count_tokens(
                    chunk.text
                )
            )

            metadata = dict(
                chunk.metadata
                if chunk.metadata
                else {}
            )

            metadata["chunk_type"] = (
                chunk.chunk_type.value
                if hasattr(
                    chunk.chunk_type,
                    "value"
                )
                else str(chunk.chunk_type)
            )

            metadata["section_path"] = (
                list(chunk.section_path)
                if chunk.section_path
                else []
            )

            document_id = metadata.get(
                "document_id"
            )

            if document_id is None:
                raise ValueError(
                    f"Missing document_id in metadata "
                    f"for chunk {chunk_index}."
                )

            document_chunk = DocumentChunk(
                document_id=document_id,
                chunk_index=chunk_index,
                chunk_text=chunk.text,
                token_count=token_count,
                embedding=embedding,
                metadata_json=metadata,
            )

            document_chunks.append(
                document_chunk
            )

        db.add_all(document_chunks)
        db.flush()

        return document_chunks