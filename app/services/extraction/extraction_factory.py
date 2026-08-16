
from app.services.extraction.base_extractor import BaseExtractor
from app.services.extraction.pdf.pdf_extractor import PdfExtractor
from app.services.extraction.docx_extractor import DocxExtractor
from app.services.extraction.markdown_extractor import MarkdownExtractor
from app.services.extraction.txt_extractor import TxtExtractor

class UnsupportedExtractorError(ValueError):
    """Raised when no extractor is registered for a document type."""

class ExtractorFactory:

    _EXTRACTOR_REGISTRY: dict[str, type[BaseExtractor]] = {
        "application/pdf": PdfExtractor,
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document":DocxExtractor,
        "text/markdown": MarkdownExtractor,
        "text/plain": TxtExtractor,
    }

    def get_extractor(self,mime_type:str)->BaseExtractor:

        if not isinstance(mime_type,str):
            raise TypeError("mime_type must be a string")

        normalized_mime_type = (mime_type.strip().lower())

        extractor_class = (self._EXTRACTOR_REGISTRY.get(normalized_mime_type))

        if extractor_class is None:
            raise UnsupportedExtractorError(
                f"No extractor registered for MIME type: "
                f"{mime_type}"
            )

        return extractor_class()

    @classmethod
    def supported_mime_types(cls)->frozenset[str]:

         """ Return all MIME types currently supported by the extraction layer."""

         return frozenset(cls._EXTRACTOR_REGISTRY.keys())

    @classmethod
    def supports(cls,mime_type: str)->bool:
        """Check whether an extractor exists for a MIME type.This does not validate the file itself."""

        if not isinstance(mime_type, str):
            return False

        return (
            mime_type.strip().lower()
            in cls._EXTRACTOR_REGISTRY
        )