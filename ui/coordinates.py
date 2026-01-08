from PySide6.QtGui import QColor

class CoordinateTransformer:
    def __init__(self):
        self.pixels_per_inch = 96.0

    def mm_to_px(self, mm):
        return (mm / 25.4) * self.pixels_per_inch
        
    def mm_to_px_tuple(self, point_mm):
        return (self.mm_to_px(point_mm[0]), self.mm_to_px(point_mm[1]))

    def get_color(self, token_name: str) -> QColor:
        """
        Retrieves a color from the theme (or fallback).
        """
        hex_code = THEME_FALLBACK.get(token_name, "#FF00FF") # Magenta = Error
        return QColor(hex_code)

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