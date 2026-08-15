from app.dto.final_chunk import FinalChunk

class MetadataEnricher:

    def enrich(self,chunks: list[FinalChunk])-> list[FinalChunk]:

        if not chunks:
            return []

        enriched_chunks: list[FinalChunk] = []

        for chunk in chunks:

            enriched_chunks.append(self._enrich_chunk(chunk))

        return enriched_chunks

    def _enrich_chunk(self,chunk:FinalChunk)->FinalChunk:

        metadata = dict(chunk.metadata)

        if not metadata and chunk.elements:
            metadata = dict(chunk.elements[0].metadata)

        return FinalChunk(
                text=chunk.text,
                elements=chunk.elements,
                chunk_type=chunk.chunk_type,
                section_path=list(chunk.section_path),
                order_index=chunk.order_index,
                metadata=metadata
            )

