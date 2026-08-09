from dataclasses import dataclass

from app.dto.document_node import DocumentNode


@dataclass
class DocumentTree:

    root: DocumentNode