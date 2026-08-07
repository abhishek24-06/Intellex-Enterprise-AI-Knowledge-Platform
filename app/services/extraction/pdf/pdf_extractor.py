from pathlib import Path

from app.dto.extraction_result import ExtractionResult
from app.services.extraction.base_extractor import BaseExtractor
from app.services.extraction.pdf.docling_extractor import DoclingExtractor


class PdfExtractor(BaseExtractor):

    def __init__(self):
        self.docling = DoclingExtractor()

    def extract(self, file_path: str | Path) -> ExtractionResult:
        return self.docling.extract(file_path)