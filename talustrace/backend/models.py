from typing import Dict, Any

class Harness:
    def __init__(self, meta: Dict[str, Any] = None):
        self.meta = meta or {}

    def to_dict(self) -> Dict[str, Any]:
        return {"meta": self.meta}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        return cls(meta=data.get("meta", {}))
