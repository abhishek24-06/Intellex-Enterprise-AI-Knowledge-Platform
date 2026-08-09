from __future__ import annotations
from dataclasses import dataclass, field

from app.dto.extracted_element import ExtractedElement

@dataclass
class DocumentNode:

    element: ExtractedElement | None

    children: list["DocumentNode"] = field(default_factory=list)

    parent: "DocumentNode | None" = None

    def add_child(self, child: "DocumentNode")-> None:

        child.parent = self

        self.children.append(child)