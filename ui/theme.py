import yaml
import os
from PySide6.QtGui import QColor

class ThemeManager:
    def __init__(self):
        self.colors = {}
        self._defaults = {
            "canvas_bg": "#23272e",
            "grid_color": "#3a3f4b",
            "device_body": "#4e5d6c",
            "device_outline": "#bfc9d1",
            "pin_fill": "#e0e0e0",
            "bundle_standard": "#8ecae6",
            "bundle_violation": "#ffb703"
        }
        self._load()

    def _load(self):
        path = "resources/config/theme.yaml"
        if not os.path.exists(path): return
        try:
            with open(path, 'r') as f:
                data = yaml.safe_load(f) or {}
                self.colors = data.get("colors", {})
        except: pass

    def get_color(self, name):
        hex_code = self.colors.get(name, self._defaults.get(name, "#FF00FF"))
        return QColor(hex_code)