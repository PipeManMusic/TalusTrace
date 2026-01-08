class HarnessSerializer:
    @staticmethod
    def to_yaml(data: dict) -> str:
        """PH5-2.2: Standard YAML serialization without Python-specific tags."""
        return yaml.safe_dump(data, sort_keys=False)

    @staticmethod
    def from_yaml(yaml_str: str) -> dict:
        """PH5-2.2: Safe loading for cross-platform compatibility."""
        return yaml.safe_load(yaml_str)
import yaml
from pathlib import Path
from core.models import Harness

class YAMLPersistence:
    """
    PH5-2.2: Infra: Harness YAML Persistence Layer
    Handles serialization/deserialization of Harness to/from YAML.
    """
    @staticmethod
    def save(harness: Harness, file_path: Path):
        with open(file_path, 'w') as f:
            yaml.dump(harness.to_dict(), f, sort_keys=False)

    @staticmethod
    def load(file_path: Path) -> Harness:
        with open(file_path, 'r') as f:
            data = yaml.safe_load(f)
        return Harness.from_dict(data)
