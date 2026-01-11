import yaml
import os
from typing import Dict, Any

class MetadataManager:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self, config_path="resources/config/device_types.yaml"):
        # Resolve path relative to THIS file (core/metadata.py) -> up one level -> resources/config
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.config_path = os.path.join(base_dir, config_path)
        self.schemas = self._load_schemas()

    def _load_schemas(self) -> Dict[str, Any]:
        if not os.path.exists(self.config_path):
            print(f">> WARNING: Metadata spec NOT FOUND at {self.config_path}")
            return {}
        
        try:
            with open(self.config_path, 'r') as f:
                data = yaml.safe_load(f)
                schemas = data.get("schemas", {})
                print(f">> SUCCESS: Loaded {len(schemas)} device schemas from YAML.")
                return schemas
        except Exception as e:
            print(f">> ERROR: Failed to load metadata schemas: {e}")
            return {}

    def get_default_metadata(self, device_type: str) -> Dict[str, Any]:
        schema = self.schemas.get(device_type, self.schemas.get("generic"))
        if not schema:
            return {}

        defaults = {}
        for key, field_def in schema.get("fields", {}).items():
            defaults[key] = field_def.get("default")
        
        defaults["_type"] = device_type
        return defaults
