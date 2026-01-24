"""
Theme loader for Talus Trace UI.

Loads theme tokens (colors, layout, canvas) from a JSON file.
"""

import json
from pathlib import Path

class ThemeLoader:
    """Loads and provides access to theme tokens for UI colors and layout."""
    def __init__(self, theme_path=None):
        """Initialize ThemeLoader with optional theme path, loading tokens from JSON."""
        if theme_path is None:
            theme_path = Path(__file__).parent.parent / "resources" / "theme_tokens.json"
        self.theme_path = Path(theme_path)
        with open(self.theme_path, "r", encoding="utf-8") as f:
            self.tokens = json.load(f)

    def get_palette_color(self, name):
        """Get a palette color by name from the loaded theme tokens."""
        return self.tokens["colors"]["palette"].get(name)

    def get_semantic_color(self, key):
        """Get a semantic color by key, resolving to palette if needed."""
        semantic = self.tokens["colors"]["semantic"]
        palette = self.tokens["colors"]["palette"]
        value = semantic.get(key)
        if value in palette:
            return palette[value]
        return value

    def get_layout_value(self, key):
        """Get a layout value by key from the loaded theme tokens."""
        return self.tokens["layout"].get(key)

    def get_canvas_value(self, key):
        """Get a canvas value by key from the loaded theme tokens."""
        return self.tokens["canvas"].get(key)
