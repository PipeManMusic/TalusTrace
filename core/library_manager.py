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
        # Resolve via the same logic used for writes so reads and writes always
        # target the same on-disk file (previously they could diverge).
        target_path = self._resolve_path(filename)

        if not os.path.exists(target_path):
            # Fail silently or log warning - return empty dict for safety
            return {}

        # Parse YAML
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

    def _resolve_path(self, filename: str) -> str:
        """Return the canonical on-disk path for a library file, matching _load_file()."""
        target_path = os.path.join(self.resource_dir, filename)
        if not os.path.exists(target_path):
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            fallback = os.path.join(base_dir, "resources", "library", filename)
            if os.path.exists(fallback) or not os.path.isdir(self.resource_dir):
                target_path = fallback
        return target_path

    def list_parts(self):
        """Return the list of part IDs currently loaded."""
        return list(self.parts.keys())

    def get_part(self, part_id: str):
        """Return the data dict for a single part, or None."""
        return self.parts.get(part_id)

    def save_part(self, part_id: str, data: Dict[str, Any]) -> str:
        """
        Persist a single part entry to parts.yaml, merging with existing parts.

        Args:
            part_id: Identifier used as the YAML key (e.g. "SPLICE-4W-SEALED").
            data: The part definition (manufacturer, pins, etc.). Must be YAML-serializable.

        Returns:
            The path the file was written to.

        Raises:
            ValueError: if ``part_id`` is empty or ``data`` is not a dict.
        """
        if not part_id or not isinstance(part_id, str):
            raise ValueError("part_id must be a non-empty string")
        if not isinstance(data, dict):
            raise ValueError("data must be a dict")

        target_path = self._resolve_path("parts.yaml")
        existing = {}
        if os.path.exists(target_path):
            try:
                with open(target_path, "r") as f:
                    loaded = yaml.safe_load(f) or {}
                existing = loaded.get("parts", loaded) or {}
            except Exception:
                existing = {}
        if not isinstance(existing, dict):
            existing = {}

        existing[part_id] = data
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        with open(target_path, "w") as f:
            yaml.safe_dump({"parts": existing}, f, sort_keys=False)

        # Refresh in-memory cache
        self.parts = existing
        return target_path

    def delete_part(self, part_id: str) -> bool:
        """
        Remove a single part entry from parts.yaml and the in-memory cache.

        Args:
            part_id: Identifier of the part to remove.

        Returns:
            True if the part existed and was removed, False if it was not found.

        Raises:
            ValueError: if ``part_id`` is empty or not a string.
        """
        if not part_id or not isinstance(part_id, str):
            raise ValueError("part_id must be a non-empty string")

        target_path = self._resolve_path("parts.yaml")
        existing = {}
        if os.path.exists(target_path):
            try:
                with open(target_path, "r") as f:
                    loaded = yaml.safe_load(f) or {}
                existing = loaded.get("parts", loaded) or {}
            except Exception:
                existing = {}
        if not isinstance(existing, dict):
            existing = {}

        if part_id not in existing:
            # Keep the in-memory cache consistent with disk before returning.
            self.parts = existing
            return False

        del existing[part_id]
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        with open(target_path, "w") as f:
            yaml.safe_dump({"parts": existing}, f, sort_keys=False)

        # Refresh in-memory cache
        self.parts = existing
        return True