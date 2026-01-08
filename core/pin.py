from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, model_validator
from core.enums import Side

class Pin(BaseModel):
    """
    The Single Source of Truth for Pin data.
    """
    id: str
    label: Optional[str] = None
    side: Side = Side.LEFT
    
    # Coordinate System (Standard)
    x: float = 0.0
    y: float = 0.0
    
    # Legacy/Routing Support
    head: List[float] = Field(default_factory=lambda: [0.0, 0.0])
    tail: List[float] = Field(default_factory=lambda: [0.0, 0.0])
    
    # Metadata
    device_id: Optional[str] = None
    net: Optional[str] = None
    meta: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = ConfigDict(populate_by_name=True, extra='ignore')

    @model_validator(mode='after')
    def set_default_label(self):
        if self.label is None:
            self.label = self.id
        return self