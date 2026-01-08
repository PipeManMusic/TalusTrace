from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict, model_validator
from core.enums import Side

class Pin(BaseModel):
    id: str
    label: Optional[str] = None
    side: Side = Side.LEFT
    
    # PHASE 6 STANDARD: Explicit float coordinates
    # Replaces legacy 'head'/'tail' lists
    x: float = 0.0
    y: float = 0.0
    
    meta: Dict[str, Any] = Field(default_factory=dict)
    
    model_config = ConfigDict(populate_by_name=True)

    @model_validator(mode='after')
    def set_default_label(self):
        if self.label is None:
            self.label = self.id
        return self

class Device(BaseModel):
    id: str
    label: Optional[str] = None
    pins: List[Pin] = Field(default_factory=list)
    x: float = 0.0
    y: float = 0.0
    rotation: float = 0.0
    revision: int = 0
    service_slack_mm: float = 50.0 
    is_ghost: bool = Field(default=False, exclude=True)
    svg_content: Optional[str] = None 
    meta: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(populate_by_name=True)