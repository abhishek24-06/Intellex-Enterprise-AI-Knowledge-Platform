from dataclasses import dataclass
from enum import Enum


class StructureType(Enum):
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
    structure_type: StructureType
    confidence: float
    scores: StructureScores