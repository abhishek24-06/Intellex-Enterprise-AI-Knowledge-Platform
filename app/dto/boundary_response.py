from dataclasses import dataclass


@dataclass
class BoundaryResponse:
    
    boundaries: list[int]