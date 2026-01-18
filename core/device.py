from pydantic.dataclasses import dataclass, ConfigDict
from typing import List, Dict, Any, Optional
from core.pin import Pin  # <--- Import Pin from the correct file


@dataclass(config=ConfigDict(validate_assignment=True))
class Device:
    id: str
    x: float = 0.0
    y: float = 0.0
    rotation: float = 0.0
    meta: Dict[str, Any] = None
    label: Optional[str] = None
    pins: List[Pin] = None
    library_id: Optional[str] = None
    revision: int = 0
    is_ghost: bool = False
    promotion_source_id: Optional[str] = None
    service_slack_mm: float = 0.0

    def __post_init__(self):
        if self.meta is None:
            self.meta = {}
        if self.pins is None:
            self.pins = []

    def model_dump(self):
        return {
            "id": self.id,
            "x": self.x,
            "y": self.y,
            "rotation": self.rotation,
            "meta": self.meta,
            "label": self.label,
            "library_id": self.library_id,
            "pins": [p.model_dump() for p in self.pins] if hasattr(self, 'pins') and self.pins else [],
            "service_slack_mm": self.service_slack_mm,
            "revision": self.revision,
            "is_ghost": self.is_ghost,
            "promotion_source_id": self.promotion_source_id
        }

    @classmethod
    def model_validate(cls, data):
        """Create a Device from a dict (for test compatibility)."""
        return cls(**data)

    def __hash__(self):
        return hash(self.id)

    def __eq__(self, other):
        if not isinstance(other, Device):
            return False
        return self.id == other.id