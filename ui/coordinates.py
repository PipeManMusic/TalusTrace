import json
from pathlib import Path
from typing import Tuple

class CoordinateTransformer:
    def __init__(self, theme_path: str = None, scale: float = None):
        # Default: 1.0 Zoom = 20 Pixels per Inch (Mandated by Canvas Spec 2.1)
        self.pixels_per_inch = 20.0 
        self.grid_size_mm = 2.0 
        from ui.theme import ThemeLoader
        self.theme = ThemeLoader(theme_path)
        if scale is not None:
            self.pixels_per_inch = float(scale)
        # Try to get scale/grid from theme if available
        try:
            dims = self.theme.tokens.get("dimensions", {})
            self.pixels_per_inch = float(dims.get("physical_scale", self.pixels_per_inch))
            self.grid_size_mm = float(dims.get("grid_size_mm", self.grid_size_mm))
        except Exception:
            pass

    def get_color(self, key):
        return self.theme.get_color(key)

    def get_dimension(self, key):
        return self.theme.get_dimension(key)

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