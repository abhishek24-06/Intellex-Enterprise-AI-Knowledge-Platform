from enum import Enum

class EmbeddingStatus(str,Enum):
    PENDING="PENDING"
    PROCESSING="PROCESSING"
    COMPLETED="COMPLETED"
    FAILED="FAILED"