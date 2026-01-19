from pydantic import BaseModel, root_validator
from core.enums import Side
from typing import Optional

class Pin(BaseModel):
    id: str
    label: Optional[str] = None
    side: Side = Side.TOP
    x: float = 0.0
    y: float = 0.0
    head: Optional[list[float]] = None
    tail: Optional[list[float]] = None
    device_id: Optional[str] = None
    signal: Optional[str] = None  # Added for properties panel compatibility

    def __init__(self, **data):
        if data.get('label') is None:
            data['label'] = data.get('id')
        super().__init__(**data)
    x: float = 0.0
    y: float = 0.0
    device_id: Optional[str] = None
    signal: Optional[str] = None  # Added for properties panel compatibility