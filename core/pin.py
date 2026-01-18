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

    @root_validator(pre=True)
    def set_label_default(cls, values):
        if values.get('label') is None:
            values['label'] = values.get('id')
        return values
    x: float = 0.0
    y: float = 0.0
    device_id: Optional[str] = None
    signal: Optional[str] = None  # Added for properties panel compatibility