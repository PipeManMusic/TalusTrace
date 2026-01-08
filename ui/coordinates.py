
import json
from pathlib import Path
from PySide6.QtGui import QColor
from typing import Tuple

class CoordinateTransformer:
    def __init__(self, theme_path: str = "resources/theme_tokens.json"):
        self.theme_data = {}
        self.pixels_per_inch = 20.0
        self.grid_size_mm = 2.0
        self.load_theme(theme_path)

    def load_theme(self, theme_path: str):
        try:
            path = Path(theme_path)
            if path.exists():
                with open(path, "r") as f:
                    self.theme_data = json.load(f)
                dims = self.theme_data.get("dimensions", {})
                self.pixels_per_inch = float(dims.get("physical_scale", self.pixels_per_inch))
                self.grid_size_mm = float(dims.get("grid_size_mm", self.grid_size_mm))
            else:
                print(f"UI_WARN: Theme file {theme_path} missing. Using Magenta Fallback.")
        except Exception as e:
            print(f"UI_ERROR: Could not parse theme: {e}")

    def get_color(self, key: str) -> QColor:
        color_hex = self.theme_data.get("colors", {}).get(key)
        if not color_hex:
            return QColor("#FF00FF")
        return QColor(color_hex)

    def get_dimension(self, key: str):
        return self.theme_data.get("dimensions", {}).get(key)

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