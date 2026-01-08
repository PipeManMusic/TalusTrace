from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from core.pin import Pin

class Device(BaseModel):
    id: str
    label: Optional[str] = None
    
    # Components
    pins: List[Pin] = Field(default_factory=list)
    
    # Spatial
    x: float = 0.0
    y: float = 0.0
    rotation: float = 0.0
    
    # Critical Fields
    revision: int = 0
    is_ghost: bool = False
    service_slack_mm: float = 50.0
    

    # Metadata
    library_id: Optional[str] = None
    promotion_source_id: Optional[str] = None  # For ancestry tracking
    meta: Dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(populate_by_name=True, extra='ignore')