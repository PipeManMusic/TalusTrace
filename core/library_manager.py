"""
LibraryManager: Loads and caches parts and wire libraries for Talus Trace.
Supports custom resource directories and YAML-based configuration.
"""
import yaml
import os
from typing import Dict, Any

class LibraryManager:
    """
    Core component responsible for loading and caching parts AND wire libraries.
    Supports a custom resource directory for testing.
    """
    def __init__(self, resource_dir="resources/library"):
        """
        Initialize the LibraryManager with a resource directory.
        Args:
            resource_dir (str): Path to the resource directory containing library YAML files.
        """
        self.resource_dir = resource_dir
        self.parts = {}
        self.wires = {}
        self.reload()

    def reload(self):
        """
        Loads both parts.yaml and wires.yaml into memory.
        """
        self.parts = self._load_file("parts.yaml")
        self.wires = self._load_file("wires.yaml")

    def _load_file(self, filename):
        """
        Helper to load a specific YAML file from the resource directory.
        Args:
            filename (str): Name of the YAML file to load.
        Returns:
            dict: Parsed YAML data from the file.
        """
        # 1. Try provided path
        target_path = os.path.join(self.resource_dir, filename)
        
        # 2. Fallback: Try relative to this script (Project Root/resources/library)
        if not os.path.exists(target_path):
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            target_path = os.path.join(base_dir, "resources", "library", filename)

        if not os.path.exists(target_path):
            # Fail silently or log warning - return empty dict for safety
            return {}

        # 3. Parse YAML
        try:
            with open(target_path, 'r') as f:
                data = yaml.safe_load(f) or {}
                # Handle nested keys (e.g. {wires: {...}}) or flat structures
                key = filename.replace('.yaml', '') # parts or wires
                return data.get(key, data)
        except Exception as e:
            return {}

    def get_parts(self) -> Dict[str, Any]:
        """
        Get the loaded parts library.
        Returns:
            dict: Parts library data.
        """
        return self.parts

    def get_wires(self) -> Dict[str, Any]:
        """
        Get the loaded wires library.
        Returns:
            dict: Wires library data.
        """
        return self.wires