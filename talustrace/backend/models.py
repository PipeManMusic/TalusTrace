from __future__ import annotations
from enum import Enum
from typing import List, Optional, Dict, Any, Tuple
from pydantic import BaseModel, Field

# --- Enums ---

class Side(str, Enum):
    """
    Defines the cardinal orientation of a Pin relative to its parent Device.
    Used for automatic layout and routing logic.
    """
    LEFT = "left"
    RIGHT = "right"
    TOP = "top"
    BOTTOM = "bottom"

# --- Sub-Models ---

class Pin(BaseModel):
    """
    Represents a connection point on a Device.
    Includes support for split geometry (Logical Head vs Physical Tail)
    for accurate formboard representation of connectors.
    """
    id: str
    label: Optional[str] = None
    side: Side = Side.LEFT
    
    # Custom Library / SVG Support
    # The 'Head' is always grid-snapped. The 'Anchor' (Tail) is the fixed
    # physical exit point defined in the SVG, relative to the Device center.
    anchor_x: Optional[float] = None
    anchor_y: Optional[float] = None
    
    meta: Dict[str, Any] = Field(default_factory=dict)

class WireLabel(BaseModel):
    text: str
    t_pos: float = 0.5  # Position along the wire (0.0 to 1.0)

class Wire(BaseModel):
    """
    Represents a logical point-to-point connection (Netlist).
    """
    id: str
    from_conn: str  # Format: "device_id.pin_id"
    to_conn: str
    color: str = "BK" # Default to Black, automotive standard
    gauge: Optional[str] = None
    
    # Geometry & Routing
    # List of (x, y) tuples defining the path.
    route: List[Tuple[float, float]] = Field(default_factory=list)
    
    # Twisted Pair Linkage
    # If True, this wire is physically inside a TwistedPair entity.
    twisted: bool = False
    pair_id: Optional[str] = None
    
    labels: List[WireLabel] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)

class Device(BaseModel):
    """
    Represents a physical component (Connector, Splice, Relay, ECU).
    Supports both procedural boxes ("AutoBox") and Custom SVG graphics.
    """
    id: str
    label: Optional[str] = None
    pins: List[Pin] = Field(default_factory=list)
    
    # Position on the Canvas
    x: float = 0.0
    y: float = 0.0
    
    # Custom Library Support
    # Raw XML/SVG string for rendering 1:1 footprint.
    svg_content: Optional[str] = None 
    
    meta: Dict[str, Any] = Field(default_factory=dict)

class TwistedPair(BaseModel):
    """
    ATOMIC ENTITY: Represents two wires twisted together.
    Unlike standard wires, this entity owns its physical termini (Anchors).
    Deleting this entity deletes the physical endpoints.
    """
    id: str
    
    # End A Configuration
    node_a: Tuple[float, float]
    rotation_a: int = 0  # 0, 90, 180, 270
    
    # End B Configuration
    node_b: Tuple[float, float]
    rotation_b: int = 180
    
    # Routing (Bezier Control Points / Elbows)
    elbows: List[Tuple[float, float]] = Field(default_factory=list)

    # Signal Data (Synced across the pair)
    # References the Wire.id of the high/low signals
    wire_id_1: Optional[str] = None 
    wire_id_2: Optional[str] = None 

# --- Root Model ---

class Harness(BaseModel):
    """
    The Root Aggregate for the entire project.
    Contains all physical and logical definitions.
    """
    # Optimistic Locking (Spec 2.1)
    # Increment on save. Reject save if incoming < current.
    revision: int = 1
    
    meta: Dict[str, Any] = Field(default_factory=dict)
    
    # Primary Containers
    devices: List[Device] = Field(default_factory=list)
    wires: List[Wire] = Field(default_factory=list)
    twisted_pairs: List[TwistedPair] = Field(default_factory=list)