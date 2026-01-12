from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from core.pin import Pin

@dataclass
class Device:
    id: str
    x: float = 0.0
    y: float = 0.0
    rotation: float = 0.0
    meta: Dict[str, Any] = field(default_factory=dict)
    
    label: Optional[str] = None
    pins: List[Pin] = field(default_factory=list)
    library_id: Optional[str] = None
    
    def __post_init__(self):
        if self.meta is None:
            self.meta = {}

    @property
    def type(self):
        return self.meta.get("type", "generic")
            
    def model_dump(self):
        return {
            "id": self.id,
            "x": self.x,
            "y": self.y,
            "rotation": self.rotation,
            "meta": self.meta.copy(),
            "label": self.label,
            "library_id": self.library_id,
            "pins": [p.model_dump() for p in self.pins] if self.pins else []
        }