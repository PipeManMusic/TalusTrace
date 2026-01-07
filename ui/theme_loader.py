import json
from pathlib import Path

class ThemeLoader:
    def __init__(self, theme_path=None):
        if theme_path is None:
            theme_path = Path(__file__).parent.parent / "resources" / "theme_tokens.json"
        self.theme_path = Path(theme_path)
        with open(self.theme_path, "r", encoding="utf-8") as f:
            self.tokens = json.load(f)

    def get_palette_color(self, name):
        return self.tokens["colors"]["palette"].get(name)

    def get_semantic_color(self, key):
        semantic = self.tokens["colors"]["semantic"]
        palette = self.tokens["colors"]["palette"]
        value = semantic.get(key)
        if value in palette:
            return palette[value]
        return value

    def get_layout_value(self, key):
        return self.tokens["layout"].get(key)

    def get_canvas_value(self, key):
        return self.tokens["canvas"].get(key)
