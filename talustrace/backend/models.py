from typing import Tuple, Optional, List, Dict, Any
from pydantic import BaseModel

class TwistedPair(BaseModel):
    id: str
    node_a: Tuple[float, float]
    node_b: Tuple[float, float]
    rotation_a: int = 0
    rotation_b: int = 0
    wire_id_1: Optional[str] = None
    wire_id_2: Optional[str] = None

class Harness(BaseModel):
    meta: Dict[str, Any] = {}
    twisted_pairs: List[TwistedPair] = []
    # Other fields and methods as needed