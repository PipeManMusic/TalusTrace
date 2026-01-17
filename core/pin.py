from pydantic import BaseModel
from typing import Optional

class Pin(BaseModel):
    id: str
    label: Optional[str] = "1"
    x: float = 0.0
    y: float = 0.0
    device_id: Optional[str] = None
    signal: Optional[str] = None  # Added for properties panel compatibility