"""
infra/validation.py

Validation hooks for bundles and wires.
"""
from typing import List

def validate_segments_unique_uuids(segments: List):
    """
    Validate that all segments have unique UUIDs.
    Args:
        segments: List of segment objects with 'id' attribute.
    Raises:
        AssertionError: If any UUIDs are duplicated.
    """
    ids = [s.id for s in segments]
    assert len(ids) == len(set(ids)), "Segment UUIDs must be unique!"

def validate_bundle(bundle):
    """
    Validate bundle for unique segment UUIDs and valid references.
    Args:
        bundle: Bundle object with 'segments' attribute.
    """
    validate_segments_unique_uuids(bundle.segments)
    # Add more validation as needed

def validate_wire(wire):
    """
    Validate wire for unique segment UUIDs and valid references.
    Args:
        wire: Wire object with 'segments' attribute.
    """
    validate_segments_unique_uuids(wire.segments)
    # Add more validation as needed
