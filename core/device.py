from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

@dataclass
class Pin:
    id: str
    x: float = 0.0
    y: float = 0.0
    label: Optional[str] = None

@dataclass
class Device:
    id: str
    x: float = 0.0
    y: float = 0.0
    rotation: float = 0.0
    # Metadata field for dynamic properties
    meta: Dict[str, Any] = field(default_factory=dict)
    
    # Optional fields
    label: Optional[str] = None
    pins: List[Pin] = field(default_factory=list)
    library_id: Optional[str] = None
    
    def __post_init__(self):
        # Ensure meta is never None
        if self.meta is None:
            self.meta = {}
            
    def model_dump(self):
        """Helper for serialization/cloning."""
        return {
            "id": self.id,
            "x": self.x,
            "y": self.y,
            "rotation": self.rotation,
            "meta": self.meta.copy(),
            "label": self.label,
            "library_id": self.library_id,
            # Simple serialization for pins if needed
            "pins": [p.__dict__ for p in self.pins] if self.pins else []
        }
