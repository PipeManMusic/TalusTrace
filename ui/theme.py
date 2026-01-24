"""
Theme utilities for Talus Trace UI.

Provides theme loading and color lookup for UI elements.
"""
import yaml
import os
from PySide6.QtGui import QColor


class ThemeManager:
    """Manages color themes for the Talus Trace UI, supporting user overrides and default values."""
    def _load_user_theme(self):
        """Attempt to load the user theme from user_path, or fallback to hardcoded defaults."""
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
        """Persist the current color overrides to the user theme file if user_path is set."""
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
        """Set a color override and persist to user_path if provided."""
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
        """Initialize ThemeManager with optional user theme path."""
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
        self._load(self.user_path or "resources/theme_tokens.json")

    def _load(self):
        """Load theme colors from user_path or default config, or fallback to defaults."""
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
        """Get a QColor for the given theme color name."""
        hex_code = self.colors.get(name, self._defaults.get(name, "#FF00FF"))
        return QColor(hex_code)

    def _load(self, path):
        """Load a theme from the given file path."""
        # ...existing code...

    def get_color(self, name):
        """Get a QColor for the given theme color name."""
        hex_code = self.colors.get(name, self._defaults.get(name, "#FF00FF"))
        return QColor(hex_code)