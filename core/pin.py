from pydantic import BaseModel, Field
from typing import Optional, Tuple, List

class Pin(BaseModel):
    """
    Core Pin model for Talus Trace.
    All coordinates are in millimeters (float, mm).
    - head: logical wiring point (mm)
    - tail: physical SVG point (mm)
    """
    id: str = Field(..., description="Unique identifier for the pin")
    head: List[float] = Field(..., description="Logical wiring point (mm)")
    tail: List[float] = Field(..., description="Physical SVG point (mm)")
    name: Optional[str] = Field(None, description="Human-readable pin name or label")
    device_id: Optional[str] = Field(None, description="Owning device UUID")
    net: Optional[str] = Field(None, description="Net/signal name this pin is connected to")
    is_ghost: bool = Field(False, description="True if the pin is a ghost (missing physical asset)")
    revision: int = Field(0, description="Revision number for optimistic locking.")

    @property
    def exit_vector(self) -> List[float]:
        """
        Returns the vector from tail to head (in mm).
        """
        return [self.head[0] - self.tail[0], self.head[1] - self.tail[1]]
