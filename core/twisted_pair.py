from typing import List, Optional
from pydantic import BaseModel, Field

class TwistedPair(BaseModel):
    id: str
    wire_ids: List[str] = Field(default_factory=list)
    turns_per_meter: int = 30
    pattern: str = "helix"
    
    # Test Compatibility Fields (Geometry placeholders)
    node_a: Optional[List[float]] = None
    node_b: Optional[List[float]] = None