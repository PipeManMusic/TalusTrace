
import yaml
import os
from PySide6.QtGui import QColor


class ThemeManager:
    def _load_user_theme(self):
        """
        Attempt to load the user theme from user_path. If not found or invalid, fallback to hardcoded defaults.
        """
        if self.user_path and os.path.exists(self.user_path):
            try:
                with open(self.user_path, 'r') as f:
                    data = yaml.safe_load(f) or {}
                    self.colors = data.get("colors", {})
                    return
            except Exception:
                pass
        # Fallback to hardcoded defaults
        from resources.defaults import DEFAULT_THEME
        self.colors = dict(DEFAULT_THEME)
    def save_user_theme(self):
        """
        Persist the current color overrides to the user theme file if user_path is set.
        """
        if self.user_path:
            import yaml
            import os
            data = {"colors": self.colors}
            os.makedirs(os.path.dirname(self.user_path), exist_ok=True)
            with open(self.user_path, 'w') as f:
                yaml.safe_dump(data, f)

    def set_color_override(self, name, value):
        """
        Set a color override and persist to user_path if provided.
        """
        self.colors[name] = value
        if self.user_path:
            # Save the override to the user theme file
            import yaml
            import os
            data = {"colors": self.colors}
            os.makedirs(os.path.dirname(self.user_path), exist_ok=True)
            with open(self.user_path, 'w') as f:
                yaml.safe_dump(data, f)

    def __init__(self, user_path=None):
        self.colors = {}
        self.user_path = user_path
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
        # Try user_path first if provided, else fallback to default path
        paths = []
        if self.user_path:
            paths.append(self.user_path)
        paths.append("resources/config/theme.yaml")
        for path in paths:
            if os.path.exists(path):
                try:
                    with open(path, 'r') as f:
                        data = yaml.safe_load(f) or {}
                        self.colors = data.get("colors", {})
                        return
                except Exception:
                    continue
        # If all fails, fallback to defaults only
        self.colors = {}

    def get_color(self, name):
        hex_code = self.colors.get(name, self._defaults.get(name, "#FF00FF"))
        return QColor(hex_code)

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