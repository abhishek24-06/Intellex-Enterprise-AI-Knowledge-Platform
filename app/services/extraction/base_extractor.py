from abc import ABC, abstractmethod

from app.dto.extraction_result import ExtractionResult

class BaseExtractor(ABC):

    @abstractmethod
    def extract(self,file_path:str)->ExtractionResult:
        """Extract structured elements from a document."""
        pass
