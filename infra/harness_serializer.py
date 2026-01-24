"""
HarnessSerializer: Serialization and deserialization utilities for harness objects in Talus Trace.
Handles conversion to and from YAML/JSON formats for persistence and interchange.
"""

import yaml

class HarnessSerializer:
    """
    Provides methods to serialize and deserialize harness objects to YAML/JSON.
    """
    @staticmethod
    def to_yaml(data):
        """Serialize a harness dict to YAML string."""
        return yaml.dump(data, sort_keys=False)

    @staticmethod
    def from_yaml(yaml_str):
        """Deserialize a YAML string to a harness dict."""
        return yaml.safe_load(yaml_str)
