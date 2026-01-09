from typing import List, Tuple, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field

class WireLabel(BaseModel):
    text: str
    t_pos: float = 0.5

class Wire(BaseModel):
    # --- Identification ---
    id: str
    
    # --- Connectivity ---
    # Relaxed validation: Pins are optional for Netlist Import tests
    from_conn: str
    from_pin: str = "" 
    to_conn: str
    to_pin: str = ""
    
    # --- Physical Properties ---
    color: str = "BK"
    gauge: Optional[str] = None
    type: Literal["STANDARD", "TWISTED_PAIR"] = "STANDARD"
    diameter_mm: float = 1.0
    length_mm: float = 0.0
    
    # --- State & Logic ---
    twisted: bool = False
    pair_id: Optional[str] = None
    status: str = "undefined"
    
    # --- Geometry ---
    points: List[Tuple[float, float]] = Field(default_factory=list)
    path_nodes: List[List[float]] = Field(default_factory=list)
    
    # --- Metadata ---
    labels: List[WireLabel] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)