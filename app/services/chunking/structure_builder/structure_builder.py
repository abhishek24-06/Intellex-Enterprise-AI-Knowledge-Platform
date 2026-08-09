from app.dto.document_tree import DocumentTree
from app.dto.document_node import DocumentNode
from app.dto.extraction_result import ExtractionResult
from app.enums.element_type import ElementType

class DocumentStructureBuilder:

    def build(self,extraction_result:ExtractionResult)->DocumentTree:

        root = DocumentNode(element=None)

        stack = [root]

        elements = sorted(extraction_result.elements,
                          key=lambda e: e.order_index)

        for element in elements:

            if element.element_type == ElementType.HEADING:

                self._handle_heading(
                    stack=stack,
                    element=element
                )
                continue
            else:
                # stack[-1] = last item in stack
                stack[-1].add_child(DocumentNode(element=element))

        return DocumentTree(root=root)

    def _handle_heading(self,stack:list[DocumentNode],element):

        node = DocumentNode(element=element)

        level = element.metadata["level"] or 1

        while(
            len(stack) > 1
            and (stack[-1].element.metadata.get("level") or 1) >= level #pop if len of stack > elements level
        ):
            stack.pop()

        stack[-1].add_child(node)
        stack.append(node)  