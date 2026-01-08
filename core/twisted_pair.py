from typing import List, Optional
from pydantic import BaseModel, Field

class TwistedPair(BaseModel):
    """
    ATOMIC ENTITY: Represents two wires twisted together.
    Extracted from models.py for Phase 6 Modular Refactor.
    """
    id: str
    
    # PH6-1.1: Coordinates standardized to List[float] [x, y]
    # Prevents !!python/tuple tags in YAML for industrial compatibility.
    node_a: List[float]
    rotation_a: int = 0
    
    node_b: List[float]
    rotation_b: int = 180
    
    # Routing (Bezier Control Points)
    # Stored as a list of coordinate lists: [[x1, y1], [x2, y2]]
    elbows: List[List[float]] = Field(default_factory=list)

    # Signal Data (Synced across the pair)
    # References the Wire.id of the high/low signals
    wire_id_1: Optional[str] = None 
    wire_id_2: Optional[str] = None