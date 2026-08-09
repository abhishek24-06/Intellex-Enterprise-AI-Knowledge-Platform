from app.dto.extracted_element import ExtractedElement
from app.dto.extraction_result import ExtractionResult
from app.enums.element_type import ElementType

from .models import StructureScores

class StructureScorer:

    HEADING_WEIGHT = 0.55
    HIERARCHY_WEIGHT = 0.35
    LIST_WEIGHT = 0.10   
    
    def score(self,extraction_result:ExtractionResult)->StructureScores:
    
        elements = extraction_result.elements
    
        if not elements:
            return StructureScores(
                structured=0.0,
                unstructured=1.0,
                tabular=0.0
            )
    
        heading_density = self._heading_density(elements)
        table_density = self._table_density(elements)
        list_density = self._list_density(elements)
        hierarchy_consistency = self._hierarchy_consistency(elements)
    
        structured_score = (
            heading_density * self.HEADING_WEIGHT
            + hierarchy_consistency * self.HIERARCHY_WEIGHT
            + list_density * self.LIST_WEIGHT
        )

        tabular_score = table_density

        unstructured_score = max(0.0, 1.0 - max(structured_score,tabular_score))

        return StructureScores(
            structured=structured_score,
            unstructured=unstructured_score,
            tabular=tabular_score
        )

    def count_headings(self,elements: list[ExtractedElement]) -> int:
        return sum(
            1
            for element in elements
            if element.element_type == ElementType.HEADING
        )

    def _heading_density(self,elements:list[ExtractedElement]) ->float:
        if not elements:
            return 0.0
        
        return self.count_headings(elements) / len(elements)

    def _table_density(self,elements:list[ExtractedElement])->float:
        if not elements:
            return 0.0
        
        table_count = sum(
            1
            for element in elements
            if element.element_type == ElementType.TABLE
        )

        return table_count / len(elements)

    def _list_density(self, elements) -> float:
        if not elements:
            return 0.0
        
        list_count = sum(
            1
            for element in elements
            if element.element_type == ElementType.LIST
        )
    
        return list_count / len(elements)

    def _hierarchy_consistency(self,elements:list[ExtractedElement])->float:

        levels = [
            element.metadata.get("level")
            for element in elements
            if(
                element.element_type == ElementType.HEADING
                and element.metadata
                and element.metadata.get("level") is not None
            )
        ]

        if len(levels) < 2:
            return 0.5

        valid_transitions = sum(
            1
            for previous,current in zip(levels,levels[1:])
            if current <= previous + 1
        )

        return valid_transitions/(len(levels)-1)
