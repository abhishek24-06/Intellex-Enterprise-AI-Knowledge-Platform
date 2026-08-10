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

        heading_text = (node.element.text
                        if node.element is not None
                        else None)

        current_path = (path + [heading_text]
                        if heading_text
                        else path)

        direct_content = [child     #Add everything in direct_content excpet Heading and ROOT node
                          for child in node.children
                          if(
                              child.element is not None
                              and child.element.element_type != ElementType.HEADING
                          )]

        narrative_elements = [
            child               #Remove Tables and Code   
            for child in direct_content
            if(
               child.element.element_type not in self.DELEGATED_TYPES
               and child.element.text.strip()
            )
        ]

        if narrative_elements:

            text = self._build_text(
                section_path=current_path,
                narrative_elements=narrative_elements
            )
            candidates.append(
                ChunkCandidate(text=text,
                               elements=[
                                   child.element
                                   for child in direct_content
                            ],
                            heading=heading_text,
                            section_path=current_path
                        )
            )

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
        
        