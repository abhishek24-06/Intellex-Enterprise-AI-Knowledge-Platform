from app.dto.chunk_context import ChunkContext
from app.dto.final_chunk import FinalChunk

class ChunkContextAttacher:

    def attach(self,chunks:list[FinalChunk],context:ChunkContext)->list[FinalChunk]:

        if not chunks:
            return []

        attached_chunks = []

        for chunk in chunks:
            metadata = dict(chunk.metadata)

            metadata.update({
                "document_id": context.document_id,
                "organization_id": context.organization_id,
                "uploaded_by": context.uploaded_by,
                "visibility": context.visibility.value,
                "document_version": context.document_version,
            })

            attached_chunks.append(
                FinalChunk(
                    text=chunk.text,
                    elements=chunk.elements,
                    chunk_type=chunk.chunk_type,
                    section_path=list(chunk.section_path),
                    order_index=chunk.order_index,
                    metadata=metadata,
                )
            )

        return attached_chunks