import json
from pathlib import Path
from typing import Tuple

class CoordinateTransformer:
    def __init__(self, theme_path: str = None, scale: float = None):
        # Default: 1.0 Zoom = 20 Pixels per Inch (Mandated by Canvas Spec 2.1)
        self.pixels_per_inch = 20.0 
        self.grid_size_mm = 2.0 
        
        if scale is not None:
            self.pixels_per_inch = float(scale)
            
        if theme_path and Path(theme_path).exists():
            with open(theme_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            dims = data.get("dimensions", {})
            self.pixels_per_inch = float(dims.get("physical_scale", self.pixels_per_inch))
            self.grid_size_mm = float(dims.get("grid_size_mm", self.grid_size_mm))

    def mm_to_px(self, mm: float) -> float:
        """
        Pixel_Pos = (Core_mm / 25.4) * Pixels_Per_Inch
        (Mandated by talus_trace_canvas_spec.md)
        """
        return (float(mm) / 25.4) * self.pixels_per_inch

    def px_to_mm(self, px: float) -> float:
        """Inverse industrial scaling for UI feedback."""
        return (float(px) / self.pixels_per_inch) * 25.4

    def mm_to_px_tuple(self, pt: Tuple[float, float]) -> Tuple[float, float]:
        """Maps coordinate pairs for high-fidelity rendering."""
        return (self.mm_to_px(pt[0]), self.mm_to_px(pt[1]))

    def snap_to_grid(self, px: float) -> float:
        """Snaps pixels to grid step derived from physical mm truth."""
        grid_px = self.mm_to_px(self.grid_size_mm)
        if grid_px == 0:
            return float(px)
        return round(px / grid_px) * grid_px