import json
from pathlib import Path
from PySide6.QtGui import QColor

# COMPLIANCE: Centralized Theme Definition (Allowed by test_ui_compliance.py)
THEME_FALLBACK = {
    "device_body": "#808080",
    "device_outline": "#000000",
    "pin_fill": "#FFFFFF",
    "bundle_standard": "#333333",
    "bundle_violation": "#FF0000",
    "wire_a": "#0000FF",
    "wire_b": "#FFA500",
    "canvas_bg": "#2E2E2E",
    "grid_color": "#444444"
}

class CoordinateTransformer:
    def __init__(self, theme_path=None):
        self.pixels_per_inch = 96.0
        self.grid_size_mm = 5.0
        self.loaded_tokens = {}
        
        if theme_path:
            self._load_theme(theme_path)

    def _load_theme(self, path):
        try:
            with open(path, 'r') as f:
                self.loaded_tokens = json.load(f)
            
            # Update Dimensions if present
            if "dimensions" in self.loaded_tokens:
                dims = self.loaded_tokens["dimensions"]
                if "physical_scale" in dims:
                    self.pixels_per_inch = float(dims["physical_scale"])
                if "grid_size_mm" in dims:
                    self.grid_size_mm = float(dims["grid_size_mm"])
                    
        except Exception as e:
            print(f"Failed to load theme from {path}: {e}")

    # --- Coordinate Math ---
    def mm_to_px(self, mm):
        return (mm / 25.4) * self.pixels_per_inch
        
    def px_to_mm(self, px):
        return (px / self.pixels_per_inch) * 25.4

    def mm_to_px_tuple(self, point_mm):
        return (self.mm_to_px(point_mm[0]), self.mm_to_px(point_mm[1]))

    def snap_to_grid(self, px_value):
        """Snaps a pixel value to the nearest grid line (defined in mm)."""
        grid_px = self.mm_to_px(self.grid_size_mm)
        if grid_px == 0: return px_value
        steps = round(px_value / grid_px)
        return steps * grid_px

    # --- Theme Lookup ---
    def get_color(self, token_name: str) -> QColor:
        """Retrieves a color from the theme (or fallback)."""
        # 1. Try loaded JSON
        if "colors" in self.loaded_tokens and token_name in self.loaded_tokens["colors"]:
            return QColor(self.loaded_tokens["colors"][token_name])
            
        # 2. Try Fallback
        hex_code = THEME_FALLBACK.get(token_name, "#FF00FF") # Magenta = Error
        return QColor(hex_code)

    def get_dimension(self, token_name: str):
        """Retrieves a numeric dimension."""
        if "dimensions" in self.loaded_tokens and token_name in self.loaded_tokens["dimensions"]:
            return self.loaded_tokens["dimensions"][token_name]
        return 0