from dataclasses import dataclass
from enum import Enum


class DocumentStructureType(Enum):
    STRUCTURED = "STRUCTURED"
    UNSTRUCTURED = "UNSTRUCTURED"
    TABULAR = "TABULAR"


@dataclass
class StructureScores:
    structured: float
    unstructured: float
    tabular: float


@dataclass
class StructureDetectionResult:
    structure_type: DocumentStructureType
    confidence: float
    scores: StructureScores