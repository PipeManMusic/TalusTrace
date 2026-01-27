"""
Device module for Talus Trace.
Defines the Device model, validation, and serialization logic.
"""

import uuid
import re

def is_valid_uuid(val):
    """
    Check if the provided value is a valid UUID string.
    Args:
        val (str): Value to check.
    Returns:
        bool: True if valid UUID, False otherwise.
    """
    uuid_regex = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
    return isinstance(val, str) and bool(uuid_regex.match(val))
from pydantic.dataclasses import dataclass, ConfigDict
from typing import List, Dict, Any, Optional
from core.pin import Pin  # <--- Import Pin from the correct file


@dataclass
class Device:
    """
    Represents a device with pins, metadata, and spatial properties.
    """
    id: str = None
    x: float = 0.0
    y: float = 0.0
    origin_x: float = 0.0
    origin_y: float = 0.0
    rotation: float = 0.0
    meta: Dict[str, Any] = None
    label: Optional[str] = None
    pins: List[Pin] = None
    library_id: Optional[str] = None
    revision: int = 0
    is_ghost: bool = False
    promotion_source_id: Optional[str] = None
    service_slack_mm: float = 0.0
    svg_body: Optional[str] = None
    internal_routing: Optional[dict] = None

    def __post_init__(self):
        """
        Initialize Device and assign a UUID if not provided. Validates UUID format and sets defaults.
        """
        if self.id is None:
            self.id = str(uuid.uuid4())
        elif not is_valid_uuid(self.id):
            raise ValueError(f"Device id must be a valid UUID, got: {self.id}")
        if self.meta is None:
            self.meta = {}
        if self.pins is None:
            self.pins = []
        if self.internal_routing is None:
            self.internal_routing = {}

    def get_pin_by_uuid(self, uuid: str):
        """
        Retrieve a pin by its UUID.
        Args:
            uuid (str): UUID of the pin to find.
        Returns:
            Pin or None: The pin if found, else None.
        """
        for pin in self.pins:
            if pin.id == uuid:
                return pin
        return None

    def add_pin(self, pin):
        """Attach a pin to this device if missing."""
        if pin not in self.pins:
            self.pins.append(pin)

    def remove_pin(self, pin_id):
        """Remove a pin by id and clean internal routing references."""
        removed = None
        remaining = []
        for pin in self.pins:
            if getattr(pin, "id", None) == pin_id and removed is None:
                removed = pin
                continue
            remaining.append(pin)
        if removed is not None:
            self.pins = remaining
            if self.internal_routing is not None:
                self.internal_routing.pop(pin_id, None)
                to_remove = [k for k, v in list(self.internal_routing.items()) if v == pin_id]
                for key in to_remove:
                    self.internal_routing.pop(key, None)
        return removed

    def to_dict(self):
        """
        Serialize the Device to a dictionary, including pins and metadata.
        Returns:
            dict: Dictionary representation of the Device.
        """
        return {
            "id": self.id,
            "x": self.x,
            "y": self.y,
            "origin_x": self.origin_x,
            "origin_y": self.origin_y,
            "rotation": self.rotation,
            "meta": self.meta,
            "label": self.label,
            "library_id": self.library_id,
            "pins": [p.to_dict() for p in self.pins],
            "service_slack_mm": self.service_slack_mm,
            "revision": self.revision,
            "is_ghost": self.is_ghost,
            "promotion_source_id": self.promotion_source_id,
            "svg_body": self.svg_body,
            "internal_routing": self.internal_routing
        }

    @classmethod
    def from_dict(cls, data):
        """
        Create a Device instance from a dictionary, including pins and metadata.
        Args:
            data (dict): Dictionary with device data.
        Returns:
            Device: New instance.
        """
        from core.pin import Pin
        pins = [Pin.from_dict(p) for p in data.get('pins', [])]
        return cls(
            id=data.get('id'),
            x=data.get('x', 0.0),
            y=data.get('y', 0.0),
            origin_x=data.get('origin_x', 0.0),
            origin_y=data.get('origin_y', 0.0),
            rotation=data.get('rotation', 0.0),
            meta=data.get('meta', {}),
            label=data.get('label'),
            pins=pins,
            library_id=data.get('library_id'),
            revision=data.get('revision', 0),
            is_ghost=data.get('is_ghost', False),
            promotion_source_id=data.get('promotion_source_id'),
            service_slack_mm=data.get('service_slack_mm', 0.0),
            svg_body=data.get('svg_body'),
            internal_routing=data.get('internal_routing', {})
        )

    @classmethod
    def model_validate(cls, data):
        """Create a Device from a dict (for test compatibility)."""
        return cls(**data)

    def __hash__(self):
        """
        Compute the hash of the Device based on its ID.
        Returns:
            int: Hash value.
        """
        return hash(self.id)

    def __eq__(self, other):
        """
        Check equality with another Device based on ID.
        Args:
            other (Device): Another device to compare.
        Returns:
            bool: True if IDs match, False otherwise.
        """
        if not isinstance(other, Device):
            return False
        return self.id == other.id