from app.dto.extraction_result import ExtractionResult

from .models import StructureDetectionResult, StructureScores, StructureType
from .scoring import StructureScorer

class StructureDetector:

    TABULAR_DOMINANCE_THRESHOLD = 0.50
    STRUCTURED_SUPPRESSION_THRESHOLD = 0.25
    STRUCTURED_MINIMUM_THRESHOLD = 0.35

    def __init__(self):

        self.scorer = StructureScorer()

    def detect(self, extraction_result:ExtractionResult)->StructureDetectionResult:

        scores = self.scorer.score(extraction_result=extraction_result)

        heading_count = self.scorer.count_headings(extraction_result.elements)

        structure_type = self._determine_structure_type(scores=scores, heading_count=heading_count)

        confidence = self._calculate_confidence(structure_type=structure_type, scores=scores)

        return StructureDetectionResult(
            structure_type=structure_type,
            confidence=confidence,
            scores=scores
        )

    def _determine_structure_type(self, scores:StructureScores, heading_count:int)->StructureType:

        if(
            scores.tabular >= self.TABULAR_DOMINANCE_THRESHOLD
            and scores.structured < self.STRUCTURED_SUPPRESSION_THRESHOLD
        ):
            return StructureType.TABULAR

        if(
            heading_count >= 2
            and scores.structured >=  self.STRUCTURED_MINIMUM_THRESHOLD
        ):
            return StructureType.STRUCTURED

        return StructureType.UNSTRUCTURED

    def _calculate_confidence(self, structure_type:StructureType, scores:StructureScores)->float:

        match structure_type:

            case  StructureType.STRUCTURED:
                return scores.structured

            case StructureType.UNSTRUCTURED:
                return scores.unstructured

            case StructureType.TABULAR:
                return  scores.tabular