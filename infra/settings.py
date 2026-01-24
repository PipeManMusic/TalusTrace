"""
SettingsManager: User/Settings CRUD and Persistence Utility
---------------------------------------------------------

Usage:
    from infra.settings import SettingsManager
    mgr = SettingsManager()  # or SettingsManager('path/to/settings.yaml')
    mgr.set('theme', 'dark')
    theme = mgr.get('theme', 'light')
    mgr.delete('theme')
    all_settings = mgr.all()

Persistence:
    - Settings are stored in YAML at the given path (default: resources/config/settings.yaml).
    - All changes are saved immediately.
    - Safe for use in CLI, API, or UI contexts.

Maintenance:
    - Add new settings keys as needed; all keys/values are supported.
    - To migrate or reset settings, delete or edit the YAML file directly.
    - For advanced use, subclass SettingsManager or extend its methods.
"""
import yaml
import os

from pathlib import Path

from pathlib import Path
class SettingsManager:
    """
    Manages user/settings CRUD and persistence.
    """
    def __init__(self, path=None):
        """
        Initialize the SettingsManager with a path to the settings file.
        Args:
            path (str, optional): Path to the settings YAML file.
        """
        self.path = Path(path or "resources/config/settings.yaml")
        self._settings = {}
        self.load()

    def load(self):
        """
        Load settings from the YAML file at self.path. If the file does not exist, initialize with empty settings.
        """
        if self.path.exists():
            with open(self.path, 'r') as f:
                self._settings = yaml.safe_load(f) or {}
        else:
            self._settings = {}

    def save(self):
        """
        Save current settings to the YAML file at self.path.
        """
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.path, 'w') as f:
            yaml.safe_dump(self._settings, f, sort_keys=False)

    def get(self, key, default=None):
        """
        Retrieve a setting value by key, returning default if not found.
        Args:
            key (str): The setting key to retrieve.
            default: Value to return if key is not found.
        Returns:
            The value associated with the key, or default if not found.
        """
        return self._settings.get(key, default)

    def set(self, key, value):
        """
        Set a setting value by key and save immediately.
        Args:
            key (str): The setting key to set.
            value: The value to assign to the key.
        """
        self._settings[key] = value
        self.save()

    def delete(self, key):
        """
        Delete a setting by key and save immediately.
        Args:
            key (str): The setting key to delete.
        """
        if key in self._settings:
            del self._settings[key]
            self.save()

    def all(self):
        """
        Return a copy of all settings as a dictionary.
        Returns:
            dict: All settings.
        """
        return dict(self._settings)

class SystemSettings:
    """
    Manages system-wide settings such as grid size, snap tolerance, and pixels per inch.
    Loads settings from configuration files.
    """
    def __init__(self):
        """
        Initialize system settings with defaults and load from config if available.
        """
        self.grid_size_mm = 5.0
        self.snap_tolerance = 0.5
        self.pixels_per_inch = 96.0
        self._load()

    def _load(self):
        """
        Load system settings from configuration files if available.
        """
        """
        Load settings from the YAML configuration file if it exists.
        """
        path = "resources/config/settings.yaml"
        if not os.path.exists(path): return
        
        try:
            with open(path, 'r') as f:
                data = yaml.safe_load(f) or {}
                ws = data.get("workspace", {})
                self.grid_size_mm = float(ws.get("grid_size_mm", 5.0))
                self.pixels_per_inch = float(ws.get("pixels_per_inch", 96.0))
        except Exception as e:
            # ...removed debug print...
            pass

    def snap(self, value_mm):
        """
        Snap a millimeter value to the nearest grid line based on grid size.
        Args:
            value_mm (float): The value in millimeters to snap.
        Returns:
            float: The snapped value.
        """
        """Snaps a millimeter value to the nearest grid line."""
        if self.grid_size_mm <= 0: return value_mm
        return round(value_mm / self.grid_size_mm) * self.grid_size_mm