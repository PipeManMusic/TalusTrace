from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, ConfigDict

class WireLabel(BaseModel):
    text: str
    t_pos: float = 0.5

class Wire(BaseModel):
    model_config = ConfigDict(extra='allow')
    # --- Identification ---
    id: str

    # --- Connectivity ---
    from_conn: str
    from_pin: str = ""
    to_conn: str
    to_pin: str = ""

    # --- Physical Properties ---
    color: str = "#808080"  # Hex color for rendering
    color_code: Optional[str] = None  # e.g., "RED/WHT" for spec compliance
    gauge: Optional[str] = None
    type: Literal["STANDARD", "TWISTED_PAIR"] = "STANDARD"
    diameter_mm: float = 1.0
    length_mm: float = 0.0

    # --- State & Logic ---
    standard_id: Optional[str] = None
    z_index: int = 0
    twisted: bool = False
    pair_id: Optional[str] = None
    status: str = "UNDEFINED"  # Draft-First default
    signal_name: Optional[str] = None  # Logical signal carried

    # --- Geometry (MM) ---
    path_nodes: List[List[float]] = Field(default_factory=list)  # Polyline in mm

    # --- Metadata ---
    labels: List[WireLabel] = Field(default_factory=list)
    meta: Dict[str, Any] = Field(default_factory=dict)

    # --- Spec Compliance & Promotion ---
    def promote_to_specified(self, standard_id: str, gauge: str, color_code: str, diameter_mm: float):
        """
        Promote wire from UNDEFINED to SPECIFIED, assigning standard, gauge, color, and diameter.
        Should be called by infra/api after user selection.
        """
        self.status = "SPECIFIED"
        self.standard_id = standard_id
        self.gauge = gauge
        self.color_code = color_code
        self.diameter_mm = diameter_mm
        # Optionally trigger audit/validation here or via infra/api

    @property
    def render_color(self) -> str:
        """
        Returns color for rendering: default theme color if UNDEFINED, else color_code or color.
        UI should use this property.
        """
        if self.status == "UNDEFINED":
            return self.meta.get("theme_wire_default", "#808080")
        return self.color_code if self.color_code else self.color

    @property
    def render_thickness(self) -> float:
        """
        Returns thickness for rendering: fixed in Diagram Mode, diameter_mm in Formboard Mode.
        UI should set mode and use this property.
        """
        mode = self.meta.get("render_mode", "diagram")
        if mode == "diagram":
            return 2.0  # px, example value
        return self.diameter_mm

    # --- Interaction Points for infra/api ---
    # - infra/api should handle grid snapping, inferred bundling, and audit triggers.
    # - core exposes geometry, status, and promote_to_specified for compliance.