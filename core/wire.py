

from pydantic import BaseModel, Field
from typing import List, Optional, Literal

class Wire(BaseModel):
    """
    Core Wire model for Talus Trace.
    - id: Unique identifier for the wire
    - source_pin_id: Pin ID at the start of the wire
    - target_pin_id: Pin ID at the end of the wire
    - type: Physical type for manufacturing (STANDARD, TWISTED_PAIR)
    - path_nodes: List of [x, y] mm lists representing the wire path (YAML/JSON compatible)
    - diameter_mm: Physical diameter for BOM/engineering
    - status: Industrial status (default 'UNDEFINED', e.g., 'CALCULATED')
    - revision: Revision number for optimistic locking
    """
    id: str = Field(..., description="Unique identifier for the wire")
    source_pin_id: str = Field(..., description="Pin ID at the start of the wire")
    target_pin_id: str = Field(..., description="Pin ID at the end of the wire")
    type: Literal["STANDARD", "TWISTED_PAIR"] = Field("STANDARD", description="Physical type for manufacturing")
    path_nodes: List[List[float]] = Field(default_factory=list, description="List of [x, y] mm lists representing the wire path (YAML/JSON compatible)")
    diameter_mm: float = Field(1.0, description="Physical diameter for BOM/engineering")
    status: str = Field("UNDEFINED", description="Industrial status (default 'UNDEFINED', e.g., 'CALCULATED')")
    revision: int = Field(0, description="Revision number for optimistic locking.")