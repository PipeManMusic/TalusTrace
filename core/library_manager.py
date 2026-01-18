import yaml
import os
from typing import Dict, Any

class LibraryManager:
    """
    Core component responsible for loading and caching the parts library.
    Strictly independent of the UI.
    """
    def __init__(self, library_path="resources/library/parts.yaml"):
        self.library_path = library_path
        self._parts_cache = {}
        self.reload()

    def reload(self):
        """Loads the YAML database into memory."""
        self._parts_cache = {}
        
        # 1. Resolve Path (Handle running from root vs subdirs)
        target_path = self.library_path
        if not os.path.exists(target_path):
            # Try finding it relative to this script (core/library_manager.py -> project_root)
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            target_path = os.path.join(base_dir, self.library_path)

        if not os.path.exists(target_path):
            # ...removed debug print...
            return

        # 2. Parse YAML
        try:
            with open(target_path, 'r') as f:
                data = yaml.safe_load(f) or {}
                self._parts_cache = self._normalize_data(data)
                # ...removed debug print...
        except Exception as e:
            # ...removed debug print...
            pass

    def get_parts(self) -> Dict[str, Any]:
        """Returns the dictionary of parts. {part_id: part_data}"""
        return self._parts_cache

    def _normalize_data(self, data):
        """
        Robustness helper: handles different YAML structures.
        Supports:
          1. { parts: { ID: {...} } }  (Standard)
          2. { ID: {...} }             (Flat)
        """
        if isinstance(data, dict):
            if "parts" in data and isinstance(data["parts"], dict):
                return data["parts"]
            return data
            
        return {}