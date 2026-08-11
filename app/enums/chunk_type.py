from enum import Enum

class ChunkType(str, Enum):
    
    NARRATIVE = "narrative"
    TABLE = "table"
    CODE = "code"