import json
from pathlib import Path
from PySide6.QtGui import QColor

class ThemeLoader:
    def __init__(self, theme_path=None):
        if theme_path is None:
            theme_path = Path(__file__).parent.parent / "resources" / "theme_tokens.json"
        self.theme_path = Path(theme_path)
        with open(self.theme_path, "r", encoding="utf-8") as f:
            self.tokens = json.load(f)

    def get_color(self, key):
        # Try semantic, then palette, then direct
        colors = self.tokens.get("colors", {})
        if "semantic" in colors and key in colors["semantic"]:
            value = colors["semantic"][key]
            # If value is a palette key, resolve
            if "palette" in colors and value in colors["palette"]:
                value = colors["palette"][value]
            return QColor(value)
        if "palette" in colors and key in colors["palette"]:
            return QColor(colors["palette"][key])
        # Fallback: direct color string
        if key in colors:
            return QColor(colors[key])
        return QColor("#000000")

    def get_dimension(self, key):
        # Try dimensions, then layout, then canvas
        if "dimensions" in self.tokens and key in self.tokens["dimensions"]:
            return self.tokens["dimensions"][key]
        if "layout" in self.tokens and key in self.tokens["layout"]:
            return self.tokens["layout"][key]
        if "canvas" in self.tokens and key in self.tokens["canvas"]:
            return self.tokens["canvas"][key]
        return None
