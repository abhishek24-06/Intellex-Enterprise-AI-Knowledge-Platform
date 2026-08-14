from dataclasses import replace

from app.dto.extracted_element import ExtractedElement
from app.dto.routed_chunk import RoutedChunk

class NarrativeSafetySplitter:

    def __init__(self,max_tokens:int = 1000):
        self.max_tokens = max_tokens

    def split(self,routed_chunk: RoutedChunk)-> list[RoutedChunk]:
            
            if not routed_chunk.elements:
                 return []

            if not routed_chunk.text or not routed_chunk.text.strip():
                 return []

            elements = sorted(routed_chunk.elements, #Sort elements based on order index
                              key=lambda element: element.order_index)

            normalized_chunk = self._rebuild_chunk(routed_chunk=routed_chunk,
                                                   elements=elements)
            
            return self._split_recursive(normalized_chunk)

    def _fits(self, text:str)-> bool:
        return len(text) <= self.max_tokens * 4 

    def _split_recursive(self,routed_chunk:RoutedChunk)-> list[RoutedChunk]:

        if self._fits(routed_chunk.text or ""): #Check if fits then return entire chunk
            return [routed_chunk]

        element_groups = self._split_by_elements(routed_chunk.elements) #if not then chunk further

        if len(element_groups) > 1: #Now if we have multiple groups 
            chunks: list[RoutedChunk] = [] #Thens store in list

            for group in element_groups: #Loop through each group

                subchunk = self._rebuild_chunk(routed_chunk=routed_chunk,elements=group)

                chunks.extend(self._split_recursive(subchunk)) #Recursive split again if not fits

            return chunks

        if len(routed_chunk.elements) == 1: #Only 1 large element
             return self._split_oversized_element(routed_chunk=routed_chunk, #Then split by line
                                                  element=routed_chunk.elements[0])

        return [routed_chunk]
    #Group element by size limit
    def _split_by_elements(self,elements:list[ExtractedElement])->list[list[ExtractedElement]]:

        if not elements:
             return []

        groups: list[list[ExtractedElement]] = [] #Store completed grp
        current_group: list[ExtractedElement] = [] #Store current grp
        current_length = 0 #Tracks no of characters in that grp

        max_chars = self.max_tokens * 4

        separator_length = 2  # "\n\n"

        for element in elements:
            text = element.text.strip()

            if not text:
                continue

            element_length = len(text) #Len of text in element

            if current_group:
                 element_length += separator_length

            if(current_group and current_length + element_length > max_chars):

                groups.append(current_group)
                current_group = []
                current_length = 0

            current_group.append(element)
            current_length += element_length

        if current_group:
             groups.append(current_group)

        return groups

    #Splits single large element
    def _split_oversized_element(self,routed_chunk: RoutedChunk,element: ExtractedElement)->list[RoutedChunk]:

        text = element.text
        parts = self._split_lines(text) #Split by lines

        if len(parts) <= 1: #if nothing produces after split keep original chunk
             return [routed_chunk]

        chunks: list[RoutedChunk] = []

        for part_index, part in enumerate(parts):
             fragment = self._create_element_fragment( #Creates variables of splitted chunks as ExtractedElement
                  element=element,
                  text=part,
                  part_index=part_index,
                  total_parts=len(parts)
             )

             chunks.append(RoutedChunk(
                  chunk_type=routed_chunk.chunk_type,
                  elements=[fragment],
                  text=part,
                  section_path=routed_chunk.section_path,
                  order_index=element.order_index
             ))

        return chunks

    def _split_lines(self,text:str,max_lines:int=40)->list[str]:

         lines = text.splitlines()

         if len(lines) <= max_lines:
              return [text]

         return[
              "\n".join(lines[i:i + max_lines])
              for i in range(0,
                             len(lines),
                             max_lines)
         ]

    def _create_element_fragment(self,
                                 element: ExtractedElement,
                                 text:str,
                                 part_index:int,
                                 total_parts:int)->ExtractedElement:

         metadata = {
            **element.metadata,
            "safety_split": True,
            "safety_split_part": part_index,
            "safety_split_total": total_parts,
            "safety_split_source_order_index": element.order_index,
        }

         return replace(element,text=text,metadata=metadata)

    def _rebuild_chunk(self,routed_chunk:RoutedChunk,elements: list[ExtractedElement])->RoutedChunk:

         text = "\n\n".join(element.text.strip()
                            for element in elements
                            if element.text and element.text.strip())

         return RoutedChunk(
              chunk_type=routed_chunk.chunk_type,
              elements=elements,
              text=text,
              section_path=routed_chunk.section_path,
              order_index=elements[0].order_index
         )
         

                     
            