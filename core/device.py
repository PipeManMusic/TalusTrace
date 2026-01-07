
from pydantic import BaseModel, Field
from typing import Optional, List, Tuple
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
