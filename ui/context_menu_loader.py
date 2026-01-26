"""
Utility to load context menu definitions from ui_layout.yaml for Talus Trace UI.
"""
import os
import yaml

UI_LAYOUT_PATH = os.path.join(os.path.dirname(__file__), '../resources/config/ui_layout.yaml')

class ContextMenuLoader:
    """Loads and provides context menu definitions from YAML for the UI."""
    _menus = None

    @classmethod
    def _load_yaml(cls):
        """Load a YAML file from the given path and return its contents as a dictionary."""
        if cls._menus is not None:
            return
        with open(UI_LAYOUT_PATH, 'r') as f:
            data = yaml.safe_load(f)
        cls._menus = data.get('context_menu', {})

    @classmethod
    def get_menu(cls, menu_type):
        """Retrieve the menu definition for the given menu name from the loaded YAML."""
        cls._load_yaml()
        return cls._menus.get(menu_type, [])
