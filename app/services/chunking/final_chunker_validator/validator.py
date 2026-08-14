from app.dto.final_chunk import FinalChunk
from app.dto.extracted_element import ExtractedElement
from app.enums.chunk_type import ChunkType


class FinalChunkValidationError(ValueError):
    """Raised when FinalChunk invariants are violated."""


class FinalChunkValidator:

    VALID_CHUNK_TYPES = {
        ChunkType.NARRATIVE,
        ChunkType.TABLE,
        ChunkType.CODE,
    }

    def validate(
        self,
        chunks: list[FinalChunk],
        source_elements: list[ExtractedElement] | None = None,
    ) -> None:
        """
        Validate the final chunk collection before downstream processing.

        source_elements is optional. When supplied, the validator also
        verifies that every source element appears in at least one final
        chunk.
        """

        self._validate_chunks(chunks)
        self._validate_order(chunks)

        if source_elements is not None:
            self._validate_source_coverage(
                chunks=chunks,
                source_elements=source_elements,
            )

    def _validate_chunks(
        self,
        chunks: list[FinalChunk],
    ) -> None:

        for index, chunk in enumerate(chunks):

            if not isinstance(chunk, FinalChunk):
                raise FinalChunkValidationError(
                    f"Invalid chunk at index {index}: "
                    f"expected FinalChunk, got {type(chunk).__name__}"
                )

            if not chunk.text or not chunk.text.strip():
                raise FinalChunkValidationError(
                    f"Chunk at index {index} has empty text"
                )

            if not chunk.elements:
                raise FinalChunkValidationError(
                    f"Chunk at index {index} has no source elements"
                )

            if not isinstance(chunk.chunk_type, ChunkType):
                raise FinalChunkValidationError(
                    f"Chunk at index {index} has invalid chunk_type: "
                    f"{chunk.chunk_type!r}"
                )

            if chunk.chunk_type not in self.VALID_CHUNK_TYPES:
                raise FinalChunkValidationError(
                    f"Chunk at index {index} has unsupported chunk_type: "
                    f"{chunk.chunk_type!r}"
                )

            if not isinstance(chunk.section_path, list):
                raise FinalChunkValidationError(
                    f"Chunk at index {index} has invalid section_path"
                )

            if not all(
                isinstance(section, str)
                for section in chunk.section_path
            ):
                raise FinalChunkValidationError(
                    f"Chunk at index {index} contains "
                    f"non-string section_path values"
                )

            if not isinstance(chunk.metadata, dict):
                raise FinalChunkValidationError(
                    f"Chunk at index {index} has invalid metadata"
                )

            if not isinstance(chunk.order_index, int):
                raise FinalChunkValidationError(
                    f"Chunk at index {index} has invalid order_index: "
                    f"{chunk.order_index!r}"
                )

            if chunk.order_index < 0:
                raise FinalChunkValidationError(
                    f"Chunk at index {index} has negative order_index: "
                    f"{chunk.order_index}"
                )

            self._validate_elements(
                chunk=chunk,
                chunk_index=index,
            )

    def _validate_elements(
        self,
        chunk: FinalChunk,
        chunk_index: int,
    ) -> None:

        seen_order_indexes: set[int] = set()

        for element in chunk.elements:

            if not isinstance(element, ExtractedElement):
                raise FinalChunkValidationError(
                    f"Chunk at index {chunk_index} contains "
                    f"an invalid source element"
                )

            if not isinstance(element.order_index, int):
                raise FinalChunkValidationError(
                    f"Chunk at index {chunk_index} contains an element "
                    f"with invalid order_index"
                )

            if element.order_index < 0:
                raise FinalChunkValidationError(
                    f"Chunk at index {chunk_index} contains an element "
                    f"with negative order_index"
                )

            if element.order_index in seen_order_indexes:
                raise FinalChunkValidationError(
                    f"Chunk at index {chunk_index} contains the same "
                    f"source element order_index more than once: "
                    f"{element.order_index}"
                )

            seen_order_indexes.add(element.order_index)

        # The chunk's position should correspond to its first
        # source element.
        minimum_order_index = min(
            element.order_index
            for element in chunk.elements
        )

        if chunk.order_index != minimum_order_index:
            raise FinalChunkValidationError(
                f"Chunk order_index {chunk.order_index} does not match "
                f"its first source element order_index "
                f"{minimum_order_index}"
            )

    def _validate_order(
        self,
        chunks: list[FinalChunk],
    ) -> None:

        for previous, current in zip(chunks, chunks[1:]):

            if current.order_index < previous.order_index:
                raise FinalChunkValidationError(
                    "Final chunks are not ordered by order_index: "
                    f"{previous.order_index} -> "
                    f"{current.order_index}"
                )

    def _validate_source_coverage(
        self,
        chunks: list[FinalChunk],
        source_elements: list[ExtractedElement],
    ) -> None:

        source_order_indexes = {
            element.order_index
            for element in source_elements
        }

        covered_order_indexes = {
            element.order_index
            for chunk in chunks
            for element in chunk.elements
        }

        missing = source_order_indexes - covered_order_indexes

        if missing:
            raise FinalChunkValidationError(
                "Source elements were lost during chunking. "
                f"Missing order_index values: {sorted(missing)}"
            )