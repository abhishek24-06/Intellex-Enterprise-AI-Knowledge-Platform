from app.dto.chunk_candidate import ChunkCandidate
from app.dto.document_node import DocumentNode
from app.dto.document_tree import DocumentTree
from app.enums.element_type import ElementType

class HierarchyChunker:

    DELEGATED_TYPES = {ElementType.TABLE,
                       ElementType.CODE_BLOCK} #tables and codes will be chunked sepeartly

    def chunk(self,document_tree: DocumentTree)-> list[ChunkCandidate]:

        candidates: list[ChunkCandidate] = []

        candidates.extend(self._chunk_section(node=document_tree.root,#Start at root of document
                                              path=[])) #Extend adds candidate one after other in existing list 

        return candidates

    def _chunk_section(self,node: DocumentNode,path: list[str])->list[ChunkCandidate]:

        candidates: list[ChunkCandidate] = []

        heading_text = (node.element.text.strip()
                        if node.element is not None and node.element.text
                        else None)

        current_path = (path + [heading_text]
                        if heading_text
                        else path)

        direct_content = [
            child
            for child in node.children
            if (
                child.element is not None
                and child.element.element_type != ElementType.HEADING
            )]
        
        meaningful_content = [
            child
            for child in direct_content
            if (
                child.element.element_type in self.DELEGATED_TYPES
                or child.element.text.strip()
            )]
        
        narrative_elements = [
            child
            for child in meaningful_content
            if child.element.element_type not in self.DELEGATED_TYPES]
        
        if meaningful_content:
        
            candidates.append(
                ChunkCandidate(
                    text=self._build_text(
                        section_path=current_path,
                        narrative_elements=narrative_elements,
                    ),
                    elements=[
                        child.element
                        for child in meaningful_content
                    ],
                    heading=heading_text,
                    section_path=current_path,
                ))

        for child  in node.children:

            if(
                child.element is not None
                and child.element.element_type == ElementType.HEADING
            ):
                candidates.extend(
                    self._chunk_section(node=child,path=current_path)
                )

        return candidates

    def _build_text(self,section_path: list[str],narrative_elements: list[DocumentNode])->str:

        parts: list[str] = []

        if section_path:
            breadcrumb = " > ".join(section_path)

            parts.append(f"Section: {breadcrumb}")

        for node in narrative_elements:

            text = node.element.text.strip()

            if text:
                parts.append(text)

        return "\n\n".join(parts)
        
        