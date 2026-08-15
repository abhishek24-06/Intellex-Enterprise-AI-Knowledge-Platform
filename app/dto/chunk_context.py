from dataclasses import dataclass

from app.enums.enums import DocumentVisibility

@dataclass(frozen=True)
class ChunkContext:
    document_id: int
    organization_id: int
    uploaded_by: int
    visibility: DocumentVisibility
    document_version: int