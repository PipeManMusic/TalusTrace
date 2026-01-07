from pydantic import BaseModel, Field
from typing import List, Tuple, Optional

class Wire(BaseModel):
    """
    Core Wire model for Talus Trace.
    - id: Unique identifier for the wire
    - source_pin_id: Pin ID at the start of the wire
    - target_pin_id: Pin ID at the end of the wire
    - path_nodes: List of (x, y) mm tuples representing the wire path
    - status: Industrial status (default 'UNDEFINED', e.g., 'CALCULATED')
    - revision: Revision number for optimistic locking
    """
    id: str = Field(..., description="Unique identifier for the wire")
    source_pin_id: str = Field(..., description="Pin ID at the start of the wire")
    target_pin_id: str = Field(..., description="Pin ID at the end of the wire")
    path_nodes: List[Tuple[float, float]] = Field(default_factory=list, description="List of (x, y) mm tuples representing the wire path")
    status: str = Field("UNDEFINED", description="Industrial status (default 'UNDEFINED', e.g., 'CALCULATED')")
    revision: int = Field(0, description="Revision number for optimistic locking.")
