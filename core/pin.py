"""
Pin dataclass and utilities for Talus Trace: UUID validation, serialization, and device pin management.
Supports enum-based side, coordinates, and metadata.
"""
import uuid
import re

def is_valid_uuid(val):
    """
    Validate that a value is a valid UUID string.
    Args:
        val (str): Value to validate.
    Returns:
        bool: True if valid UUID, else False.
    """
    uuid_regex = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
    return isinstance(val, str) and bool(uuid_regex.match(val))
from dataclasses import dataclass, field
from core.enums import Side
from typing import Optional


@dataclass
class Pin:
    """
    Represents a device pin with coordinates, side, metadata, and UUID.
    Supports serialization and validation.
    """
    side: Side = Side.TOP
    x: float = 0.0
    y: float = 0.0
    head: Optional[list[float]] = None
    tail: Optional[list[float]] = None
    device_id: Optional[str] = None
    signal: Optional[str] = None  # Added for properties panel compatibility
    meta: dict = field(default_factory=dict)
    id: Optional[str] = None
    label: Optional[str] = None

    def __post_init__(self):
        """
        Initialize the pin, generating a UUID and label if not provided, and validate UUID.
        Raises ValueError if id is not a valid UUID.
        """
        if self.id is None:
            self.id = str(uuid.uuid4())
        elif not is_valid_uuid(self.id):
            raise ValueError(f"Pin id must be a valid UUID, got: {self.id}")
        if self.label is None:
            self.label = self.id

    def to_dict(self):
        """
        Serialize the pin to a dictionary.
        Returns:
            dict: Dictionary representation of the pin.
        """
        return {
            'side': self.side.value if hasattr(self.side, 'value') else self.side,
            'x': self.x,
            'y': self.y,
            'head': self.head,
            'tail': self.tail,
            'device_id': self.device_id,
            'signal': self.signal,
            'meta': self.meta,
            'id': self.id,
            'label': self.label
        }

    @classmethod
    def from_dict(cls, data):
        """
        Create a Pin instance from a dictionary.
        Args:
            data (dict): Dictionary containing pin fields.
        Returns:
            Pin: Instance created from the dictionary.
        """
        from core.enums import Side
        side = data.get('side', Side.TOP)
        if isinstance(side, str):
            # Accept both enum names ("TOP") and values ("top")
            try:
                side = Side[side]
            except KeyError:
                try:
                    side = Side(side)
                except ValueError:
                    side = Side.TOP
        return cls(
            side=side,
            x=data.get('x', 0.0),
            y=data.get('y', 0.0),
            head=data.get('head'),
            tail=data.get('tail'),
            device_id=data.get('device_id'),
            signal=data.get('signal'),
            meta=data.get('meta', {}),
            id=data.get('id'),
            label=data.get('label')
        )