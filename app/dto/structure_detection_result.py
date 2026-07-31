from dataclasses import dataclass

from app.enums.chunking_startegy import ChunkingStrategy

@dataclass(slots=True)
class StructureDetectionResult:

    strategy:ChunkingStrategy
    confidence:float
    structured_score:float
    unstructured_score:float
    tabular_score:float

