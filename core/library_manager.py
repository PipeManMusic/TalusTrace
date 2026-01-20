import yaml
import os
from typing import Dict, Any

class LibraryManager:
    """
    Core component responsible for loading and caching parts AND wire libraries.
    Supports a custom resource directory for testing.
    """
    def __init__(self, resource_dir="resources/library"):
        self.resource_dir = resource_dir
        self.parts = {}
        self.wires = {}
        self.reload()

    def reload(self):
        """Loads both parts.yaml and wires.yaml into memory."""
        self.parts = self._load_file("parts.yaml")
        self.wires = self._load_file("wires.yaml")

    def _load_file(self, filename):
        """Helper to load a specific YAML file from the resource directory."""
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
            print(f"[LibraryManager] Error loading {filename}: {e}")
            return {}

    def get_parts(self) -> Dict[str, Any]:
        return self.parts

    def get_wires(self) -> Dict[str, Any]:
        return self.wires