from pydantic import BaseModel, Field
from typing import Optional, List, Tuple, Dict
from core.pin import Pin


class Device(BaseModel):
    meta: dict = Field(default_factory=dict, description="Arbitrary device metadata, e.g. width_mm, height_mm")
    """
    Core Device model for Talus Trace.
    - name: Human-readable device name
    - pos: (x, y) position in mm
    - pins: List of Pin objects
    - rotation: Device rotation in degrees (float)
    - is_generic: True if this is a temporary DIY "Napkin" device.
    - is_ghost: True if the physical asset (SVG) is missing; triggers ghost rendering.
    - library_id: Reference to the master YAML in the library.
    - promotion_source_id: Links an industrial device back to its generic ancestor.
    - revision: Revision number for optimistic locking.
    """
    id: str = Field(..., description="Unique identifier for the device")
    name: Optional[str] = Field(None, description="Human-readable device name")
    pos: Optional[Tuple[float, float]] = Field(None, description="Device position (mm)")
    pins: Optional[List[Pin]] = Field(default_factory=list, description="List of Pin objects")
    rotation: float = Field(0.0, description="Device rotation in degrees")
    is_generic: bool = Field(False, description="True if this is a temporary DIY 'Napkin' device.")
    is_ghost: bool = Field(True, description="True if the physical asset (SVG) is missing; triggers ghost rendering.")
    library_id: Optional[str] = Field(None, description="Reference to the master YAML in the library.")
    promotion_source_id: Optional[str] = Field(None, description="Links an industrial device back to its generic ancestor.")
    revision: int = Field(0, description="Revision number for optimistic locking.")

class Connector(Device):
    rows: int = Field(..., description="Number of pin rows")
    cols: int = Field(..., description="Number of pin columns")
    pitch_mm: float = Field(..., description="Pin pitch in mm")
    pins: Dict[str, Pin] = Field(default_factory=dict, description="Grid of Pin objects indexed by 'row:col'")

    def __init__(self, **data):
        super().__init__(**data)
        # Auto-generate pin grid
        pins = {}
        for r in range(1, self.rows + 1):
            for c in range(1, self.cols + 1):
                pin_id = f"{r}:{c}"
                x_mm = (c - 1) * self.pitch_mm
                y_mm = (r - 1) * self.pitch_mm
                pins[pin_id] = Pin(
                    id=f"{self.id}:{pin_id}",
                    head=(x_mm, y_mm),
                    tail=(x_mm, y_mm),
                    name=pin_id,
                    device_id=self.id
                )
        self.pins = pins
