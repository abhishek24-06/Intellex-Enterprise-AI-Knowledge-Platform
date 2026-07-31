from dataclasses import dataclass, field
from typing import Any

from app.enums.element_type import ElementType

@dataclass(slots=True) #Auto-generate methods + save memory
class ExtractedElement:
    order_index:int
    text:str
    element_type:ElementType
    metadata:dict[str,Any]=field(default_factory=dict) #new empt dict for every new element