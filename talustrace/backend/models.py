from enum import Enum
from typing import List, Optional, Tuple, Union, Dict, Any
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict

# --- Enums for Strict Typing ---
class DeviceType(str, Enum):
    AUTO_BOX = "AutoBox"          # Dynamic Size (Text + Pins)
    SVG_TEMPLATE = "SVG_Template" # Loaded from assets/

class Side(str, Enum):
    LEFT = "left"
    RIGHT = "right"
    TOP = "top"
    BOTTOM = "bottom"

# --- Sub-Components ---
class Pin(BaseModel):
    id: str
    label: Optional[str] = None
    side: Side = Side.LEFT

class WireRoute(BaseModel):
    """Represents the physical path of a wire as a series of elbows."""
    points: List[Tuple[float, float]] = []  # [(x1, y1), (x2, y2)...]

# --- Main Components ---
class Device(BaseModel):
    id: str = Field(..., description="Unique Device ID (e.g. 'ECU')")
    type: DeviceType = DeviceType.AUTO_BOX
    label: str = Field(..., description="Human readable label (e.g. 'MS3Pro')")
    pins: Union[List[Pin], int] = Field(..., description="List of pins OR count")
    
    # Physical placement on canvas (Optional, defaults to 0,0)
    x: float = 0.0
    y: float = 0.0

    @field_validator('pins')
    @classmethod
    def validate_pins(cls, v):
        """If user provides an int (e.g. pins: 12), auto-generate Pin objects alternating L/R."""
        if isinstance(v, int):
            return [
                Pin(
                    id=str(i+1), 
                    side=Side.LEFT if i % 2 == 0 else Side.RIGHT
                ) 
                for i in range(v)
            ]
        return v

class Wire(BaseModel):
    # ALLOWS using 'from_conn' instead of the alias 'from'
    model_config = ConfigDict(populate_by_name=True)

    id: str = Field(..., description="Unique Wire ID (e.g. 'W-101')")
    from_conn: str = Field(..., alias="from", description="Format: 'DeviceID.PinID'")
    to_conn: str = Field(..., alias="to", description="Format: 'DeviceID.PinID'")
    
    # Physical Attributes
    color: str = "WH"
    stripe: Optional[str] = None
    gauge: Union[int, str] = 18
    
    # Logic & Fabrication
    signal: Optional[str] = None  # The "Signal Name" for Label Generation
    route: List[Tuple[float, float]] = [] # User-defined elbows

    @model_validator(mode='after')
    def validate_endpoints(self):
        """Ensure endpoints follow 'Device.Pin' format."""
        if '.' not in self.from_conn or '.' not in self.to_conn:
            raise ValueError("Endpoints must be 'DeviceID.PinID'")
        return self

# --- The Root Document ---
class Harness(BaseModel):
    meta: Dict[str, Any] = {}
    settings: Dict[str, Any] = {"grid_size": 20}
    devices: List[Device] = []
    wires: List[Wire] = []