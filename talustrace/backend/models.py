from pydantic import BaseModel, Field
from typing import Tuple, Optional, List, Dict, Any

class TwistedPair(BaseModel):
    id: str
    node_a: Tuple[float, float]
    node_b: Tuple[float, float]
    rotation_a: int = 0
    rotation_b: int = 180
    wire_id_1: Optional[str] = None
    wire_id_2: Optional[str] = None

class Harness(BaseModel):
    meta: Dict[str, Any] = Field(default_factory=dict)
    twisted_pairs: List[TwistedPair] = Field(default_factory=list)