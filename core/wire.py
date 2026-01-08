from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field

class WireLabel(BaseModel):
    text: str
    t_pos: float = 0.5

class Wire(BaseModel):
    id: str
    from_conn: str
    to_conn: str
    color: str = "BK"
    gauge: Optional[str] = None
    
    # Manufacturing Metadata
    type: Literal["STANDARD", "TWISTED_PAIR"] = "STANDARD"
    diameter_mm: float = 1.0
    
    # Geometry: List[List[float]]
    path_nodes: List[List[float]] = Field(default_factory=list)
    
    twisted: bool = False
    pair_id: Optional[str] = None
    status: str = "undefined"
    
    labels: List[WireLabel] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)