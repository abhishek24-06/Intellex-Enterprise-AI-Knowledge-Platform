from enum import Enum

class ChunkingStrategy(str, Enum):
    STRUCTURED = "STRUCTURED"
    UNSTRUCTURED = "UNSTRUCTURED"
    TABULAR = "TABULAR"
    


