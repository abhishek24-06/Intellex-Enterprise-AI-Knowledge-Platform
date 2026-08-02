from enum import Enum

class ElementType(str, Enum):
    TITLE = "TITLE"
    HEADING = "HEADING"
    PARAGRAPH = "PARAGRAPH"
    TABLE = "TABLE"
    LIST = "LIST"
    QUOTE = "QUOTE"
    CODE_BLOCK = "CODE_BLOCK"
    CAPTION = "CAPTION"
    IMAGE = "IMAGE"
    UNKNOWN = "UNKNOWN"