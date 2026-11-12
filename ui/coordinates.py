"""
Coordinate transformation and theme color utilities for Talus Trace UI.

Provides pixel/mm conversion, grid snapping, and theme color/dimension lookup.
"""

import json
from pathlib import Path
from PySide6.QtGui import QColor

# COMPLIANCE: Centralized Theme Definition
THEME_FALLBACK = {
    "canvas_bg": "#121212",
    "grid_color": "#2d2d2d",
    "grid_minor": "#1e1e1e",
    "grid_major": "#333333",
    "device_body": "#1e1e1e",
    "device_outline": "#b0b0b0",
    "pin_fill": "#e0e0e0",
    "pin_outline": "#b0b0b0",
    "pin_label": "#b0b0b0",
    "bundle_standard": "#D94E1F",
    "bundle_violation": "#dc3545",
    "wire_a": "#D94E1F",
    "wire_b": "#FF6B3B",
    "selection_glow": "#00C8FF",
    "selection_highlight": "#00B4FF",
    "elbow_grip": "#FFC800",
    "segment_grip": "#00C8FF",
    "ui_bg_dark": "#121212",
    "ui_bg_light": "#1e1e1e",
    "ui_surface": "#2d2d2d",
    "ui_border": "#333333",
    "ui_text": "#e0e0e0",
    "ui_text_dim": "#b0b0b0",
    "ui_text_bright": "#ffffff",
    "ui_accent": "#D94E1F",
    "ui_hover": "#FF6B3B",
    "ui_disabled": "#666666",
    "ui_shadow": "#000000"
}

"""
Coordinate transformation and theme color utilities for Talus Trace UI.

Provides pixel/mm conversion, grid snapping, and theme color/dimension lookup.
"""

class CoordinateTransformer:
    """Handles coordinate conversions and theme lookups for the UI grid and device rendering."""
    def __init__(self, theme_path=None):
        """Initialize transformer with optional theme file path."""
        self.pixels_per_inch = 96.0
        self.grid_size_mm = 5.0
        self.loaded_tokens = {}
        
        if theme_path:
            self._load_theme(theme_path)

    def _load_theme(self, path):
        """Load theme tokens (colors, dimensions) from a JSON file."""
        try:
            with open(path, 'r') as f:
                self.loaded_tokens = json.load(f)
            
            if "dimensions" in self.loaded_tokens:
                dims = self.loaded_tokens["dimensions"]
                if "physical_scale" in dims:
                    self.pixels_per_inch = float(dims["physical_scale"])
                if "grid_size_mm" in dims:
                    self.grid_size_mm = float(dims["grid_size_mm"])
                    
        except Exception as e:
            # ...removed debug print...
            pass

    # --- Coordinate Math ---
    def mm_to_px(self, mm):
        """Convert millimeters to pixels using the current scale."""
        return (mm / 25.4) * self.pixels_per_inch
        
    def px_to_mm(self, px):
        """Convert pixels to millimeters using the current scale."""
        return (px / self.pixels_per_inch) * 25.4

    def mm_to_px_tuple(self, point_mm):
        """Convert a (mm, mm) tuple to (px, px)."""
        return (self.mm_to_px(point_mm[0]), self.mm_to_px(point_mm[1]))

    def snap_to_grid(self, px_value):
        """Snap a pixel value to the nearest grid line."""
        """Snaps a pixel value to the nearest grid line (calculated from mm)."""
        grid_px = self.mm_to_px(self.grid_size_mm)
        if grid_px == 0: return px_value
        steps = round(px_value / grid_px)
        return steps * grid_px

    def snap_mm(self, mm_value):
        """Snap a millimeter value to the nearest grid line."""
        """Snaps a millimeter value to the nearest grid line (in mm)."""
        if self.grid_size_mm == 0: return mm_value
        steps = round(mm_value / self.grid_size_mm)
        return steps * self.grid_size_mm

    # --- Theme Lookup ---
    def get_color(self, token_name: str) -> QColor:
        """Get a QColor for the given theme token name."""
        if "colors" in self.loaded_tokens and token_name in self.loaded_tokens["colors"]:
            return QColor(self.loaded_tokens["colors"][token_name])
        hex_code = THEME_FALLBACK.get(token_name, "#FF00FF") 
        return QColor(hex_code)

    def get_dimension(self, token_name: str):
        """Get a dimension value from the loaded theme, or 0 if not found."""
        if "dimensions" in self.loaded_tokens and token_name in self.loaded_tokens["dimensions"]:
            return self.loaded_tokens["dimensions"][token_name]
        return 0