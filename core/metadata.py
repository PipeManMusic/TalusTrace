"""
Metadata module for Talus Trace.
Handles loading and management of device metadata schemas.
"""
import yaml
import os
from typing import Dict, Any

class MetadataManager:
    """
    Singleton manager for device metadata schemas and defaults.
    """
    _instance = None

    @classmethod
    def get_instance(cls):
        """
        Get or create the singleton instance of MetadataManager.
        Returns:
            MetadataManager: The singleton instance.
        """
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self, config_path="resources/config/device_types.yaml"):
        """
        Initialize MetadataManager and load schemas from config file.
        Args:
            config_path (str): Path to the device types YAML config.
        """
        # Resolve path relative to THIS file (core/metadata.py) -> up one level -> resources/config
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.config_path = os.path.join(base_dir, config_path)
        self.schemas = self._load_schemas()

    def _load_schemas(self) -> Dict[str, Any]:
        """
        Load device schemas from the YAML config file.
        Returns:
            dict: Loaded schemas.
        """
        if not os.path.exists(self.config_path):
            return {}
        
        try:
            with open(self.config_path, 'r') as f:
                data = yaml.safe_load(f)
                schemas = data.get("schemas", {})
                return schemas
        except Exception as e:
            return {}

    def get_default_metadata(self, device_type: str) -> Dict[str, Any]:
        """
        Get default metadata for a given device type.
        Args:
            device_type (str): Type of device.
        Returns:
            dict: Default metadata values.
        """
        schema = self.schemas.get(device_type, self.schemas.get("generic"))
        if not schema:
            return {}

        defaults = {}
        for key, field_def in schema.get("fields", {}).items():
            defaults[key] = field_def.get("default")
        
        defaults["_type"] = device_type
        return defaults
