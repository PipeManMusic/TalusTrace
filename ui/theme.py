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