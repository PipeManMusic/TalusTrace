from pydantic import BaseModel, field_validator
from typing import Tuple, Optional

# --- Atomic Twisted Pair ---
class TwistedPair(BaseModel):
    id: str
    node_a: Tuple[float, float]
    node_b: Tuple[float, float]
    rotation_a: int = 0
    rotation_b: int = 0
    wire_id_1: Optional[str] = None
    wire_id_2: Optional[str] = None

    @field_validator('node_a', 'node_b')
    @classmethod
    def validate_coords(cls, v):
        if not (isinstance(v, tuple) and len(v) == 2 and all(isinstance(x, (int, float)) for x in v)):
            raise ValueError('node_a and node_b must be (float, float) tuples')
        return v
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
    meta: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def default_label(self):
        # Ensure every pin carries a user-visible label; fallback to id when omitted.
        if not self.label:
            self.label = self.id
        return self

class WireRoute(BaseModel):
    """Represents the physical path of a wire as a series of elbows."""
    points: List[Tuple[float, float]] = Field(default_factory=list)  # [(x1, y1), (x2, y2)...]

# --- Main Components ---
class Device(BaseModel):
    id: str = Field(..., description="Unique Device ID (e.g. 'ECU')")
    type: DeviceType = DeviceType.AUTO_BOX
    label: str = Field(..., description="Human readable label (e.g. 'MS3Pro')")
    pins: Union[List[Pin], int] = Field(..., description="List of pins OR count")
    meta: Dict[str, Any] = Field(default_factory=dict)
    
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
                    label=str(i+1),
                    side=Side.LEFT if i % 2 == 0 else Side.RIGHT
                ) 
                for i in range(v)
            ]
        return v

class WireLabel(BaseModel):
    text: str = Field(..., description="Label text")
    t_pos: float = Field(0.5, description="Normalized position along the wire (0.0 - 1.0)")
    align: Optional[str] = None
    style: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode='after')
    def clamp_t(self):
        try:
            if self.t_pos < 0.0:
                self.t_pos = 0.0
            if self.t_pos > 1.0:
                self.t_pos = 1.0
        except Exception:
            pass
        return self


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
    twisted: bool = False
    pair_id: Optional[str] = None
    
    # Logic & Fabrication
    signal: Optional[str] = None  # The "Signal Name" for Label Generation
    meta: Dict[str, Any] = Field(default_factory=dict)
    route: List[Tuple[float, float]] = Field(default_factory=list) # User-defined elbows
    labels: List[WireLabel] = Field(default_factory=list)  # Floating label list

    @model_validator(mode='after')
    def validate_endpoints(self):
        """Ensure endpoints follow 'Device.Pin' format."""
        if '.' not in self.from_conn or '.' not in self.to_conn:
            raise ValueError("Endpoints must be 'DeviceID.PinID'")
        return self

class TwistNode(BaseModel):
    id: str
    x: float = 0.0
    y: float = 0.0

class TwistedBundle(BaseModel):
    id: str
    from_node: str
    to_node: str
    elbow: Tuple[float, float]
    amplitude: Optional[float] = None
    wavelength: Optional[float] = None

# --- The Root Document ---
class Harness(BaseModel):
    meta: Dict[str, Any] = Field(default_factory=dict)
    settings: Dict[str, Any] = Field(default_factory=lambda: {"grid_size": 20})
    devices: List[Device] = Field(default_factory=list)
    wires: List[Wire] = Field(default_factory=list)
    twist_nodes: List[TwistNode] = Field(default_factory=list)
    bundles: List[TwistedBundle] = Field(default_factory=list)