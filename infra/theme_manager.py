"""
ThemeManager: Theme Switching and Serialization Utility
------------------------------------------------------

Usage:
    from infra.theme_manager import ThemeManager
    mgr = ThemeManager()
    mgr.set_theme('default')
    mgr.set_theme('custom')
    theme = mgr.get_theme()
    all_themes = mgr.list_themes()

Persistence:
    - Selected theme is stored in resources/config/theme.yaml (YAML, as 'active_theme').
    - Custom theme definitions are loaded from resources/config/theme.yaml.
    - Default theme is loaded from resources/theme_tokens.json.

Maintenance:
    - Add new themes by extending the resources or ThemeManager logic.
    - For advanced use, subclass ThemeManager or extend its methods.
"""
import json
from pathlib import Path

import yaml

class ThemeManager:
    """
    Manages theme switching, serialization, and persistence for Talus Trace.
    Loads default and custom themes, tracks active theme, and provides theme utilities.
    """

    def load_theme_from_json(self, json_str, name='custom'):
        """
        Load a theme from a JSON string and add/update it in the theme manager.
        Args:
            json_str (str): JSON string containing theme data.
            name (str): Name to assign to the loaded theme (default: 'custom').
        Returns:
            dict: The loaded theme dict, always with a 'colors' key.
        """
        theme_data = json.loads(json_str)
        # Always wrap in a dict with 'colors' if not already
        if not (isinstance(theme_data, dict) and 'colors' in theme_data):
            theme_data = {'colors': theme_data}
        self._themes[name] = theme_data
        self._active_theme = name
        # Optionally persist the theme
        data = {}
        if self.CUSTOM_THEME_PATH.exists():
            with open(self.CUSTOM_THEME_PATH) as f:
                data = yaml.safe_load(f) or {}
        data['colors'] = theme_data['colors']
        data['active_theme'] = name
        with open(self.CUSTOM_THEME_PATH, 'w') as f:
            yaml.safe_dump(data, f, sort_keys=False)
        return theme_data
    DEFAULT_THEME = 'default'
    DEFAULT_THEME_PATH = Path('resources/theme_tokens.json')
    CUSTOM_THEME_PATH = Path('resources/config/theme.yaml')

    def __init__(self):
        """
        Initialize the ThemeManager, load available themes, and set the active theme.
        """
        self._themes = {}
        self._active_theme = self.DEFAULT_THEME
        self._load_themes()
        self._load_active_theme()

    def _load_themes(self):
        """
        Load default and custom themes from their respective files.
        """
        # Load default theme
        if self.DEFAULT_THEME_PATH.exists():
            with open(self.DEFAULT_THEME_PATH) as f:
                self._themes['default'] = json.load(f)
        # Load custom theme if present
        if self.CUSTOM_THEME_PATH.exists():
            with open(self.CUSTOM_THEME_PATH) as f:
                data = yaml.safe_load(f) or {}
                if 'colors' in data:
                    self._themes['custom'] = data
                if 'active_theme' in data:
                    self._active_theme = data['active_theme']

    def _load_active_theme(self):
        """
        Load the active theme from the custom theme file if specified.
        """
        # If custom theme.yaml has active_theme, use it
        if self.CUSTOM_THEME_PATH.exists():
            with open(self.CUSTOM_THEME_PATH) as f:
                data = yaml.safe_load(f) or {}
                if 'active_theme' in data:
                    self._active_theme = data['active_theme']

    def list_themes(self):
        """
        List all available theme names.
        Returns:
            list: Names of available themes.
        """
        return list(self._themes.keys())

    def get_theme(self):
        """
        Get the currently active theme data.
        Returns:
            dict: Theme data for the active theme, always with a 'colors' key and 'device_body' present.
        """
        theme = self._themes.get(self._active_theme)
        if theme is None:
            theme = self._themes.get(self.DEFAULT_THEME, {})
        # Always ensure theme is a dict with 'colors' key
        if not isinstance(theme, dict):
            theme = {'colors': {}}
        if 'colors' not in theme or theme['colors'] is None:
            theme['colors'] = {}
        # Merge missing color keys from default theme
        default_theme = self._themes.get(self.DEFAULT_THEME, {})
        default_colors = default_theme.get('colors', {}) if isinstance(default_theme, dict) else {}
        for k, v in default_colors.items():
            if k not in theme['colors'] or theme['colors'][k] is None:
                theme['colors'][k] = v
        # Ensure 'device_body' is always present
        if 'device_body' not in theme['colors'] or not theme['colors']['device_body']:
            theme['colors']['device_body'] = default_colors.get('device_body', '#FDFDFD')
        return theme

    def set_theme(self, name):
        """
        Set the active theme by name and persist the selection.
        Args:
            name (str): Name of the theme to activate.
        Raises:
            ValueError: If the theme name is not found.
        """
        if name not in self._themes:
            raise ValueError(f"Theme '{name}' not found.")
        self._active_theme = name
        # Persist active theme selection
        data = {}
        if self.CUSTOM_THEME_PATH.exists():
            with open(self.CUSTOM_THEME_PATH) as f:
                data = yaml.safe_load(f) or {}
        data['active_theme'] = name
        # Always ensure 'colors' is present for the active theme
        theme = self._themes.get(name, {})
        if 'colors' in theme:
            data['colors'] = theme['colors']
        with open(self.CUSTOM_THEME_PATH, 'w') as f:
            yaml.safe_dump(data, f, sort_keys=False)

    def serialize_theme(self, name=None):
        """
        Serialize the specified theme to a JSON string.
        Args:
            name (str, optional): Name of the theme to serialize. Defaults to active theme.
        Returns:
            str: Serialized theme data as JSON string.
        """
        name = name or self._active_theme
        # If custom theme.yaml has active_theme, use it
        if self.CUSTOM_THEME_PATH.exists():
            with open(self.CUSTOM_THEME_PATH) as f:
                data = yaml.safe_load(f) or {}
                if 'colors' in data:
                    self._themes['custom'] = data
                if 'active_theme' in data:
                    self._active_theme = data['active_theme']
        theme_data = self._themes.get(name, self._themes.get(self.DEFAULT_THEME, {'colors': {}}))
        if not isinstance(theme_data, dict):
            theme_data = {'colors': {}}
        if 'colors' not in theme_data or theme_data['colors'] is None:
            theme_data['colors'] = {}
        return json.dumps(theme_data)
