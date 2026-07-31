from enum import Enum

class ElementType(str, Enum):
    TITLE = "TITLE"
    HEADING = "HEADING"
    PARAGRAPH = "PARAGRAPH"
    TABLE = "TABLE"
    LIST = "LIST"
    QUOTE = "QUOTE"
    CODE = "CODE"
    CAPTION = "CAPTION"
    IMAGE = "IMAGE"
    UNKNOWN = "UNKNOWN"