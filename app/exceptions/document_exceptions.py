class DocumentExtractionError(Exception):
    """Raised when document text extraction fails."""


class UnsupportedDocumentTypeError(DocumentExtractionError):
    """Raised when the document type is not supported."""


class EmptyDocumentError(DocumentExtractionError):
    """Raised when no text could be extracted."""