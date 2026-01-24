"""
infra/segment_utils.py

Shared utilities for segment UUID management, comparison, and validation for wires and bundles.
"""
import uuid
from typing import List, Any, Set
from typing import Callable

# Test hook: allows tests to override the UUID generator
_uuid_generator: Callable[[], str] = lambda: str(uuid.uuid4())

def generate_uuid() -> str:
    """
    Generate a new UUID string using the current generator.
    Returns:
        str: A new UUID string.
    """
    return _uuid_generator()

def ensure_unique_uuids(segments: List[Any], id_attr: str = 'id'):
    """
    Ensures all segments in the list have unique UUIDs. If duplicates are found, assigns new UUIDs.
    Args:
        segments (List[Any]): List of segment objects.
        id_attr (str): Attribute name for the UUID.
    """
    seen: Set[str] = set()
    for seg in segments:
        seg_id = getattr(seg, id_attr)
        if seg_id in seen:
            setattr(seg, id_attr, generate_uuid())
        seen.add(getattr(seg, id_attr))

def restore_uuids_by_key(new_segments: List[Any], old_segments: List[Any], key_fn, id_attr: str = 'id'):
    """
    For each segment in new_segments, if its key matches one in old_segments, restore its UUID.
    Args:
        new_segments (List[Any]): New segment objects.
        old_segments (List[Any]): Old segment objects.
        key_fn (callable): Function to extract key from segment.
        id_attr (str): Attribute name for the UUID.
    """
    old_key_map = {}
    for s in old_segments:
        try:
            k = key_fn(s)
        except Exception:
            continue
        if k is not None:
            old_key_map[k] = getattr(s, id_attr)
    for seg in new_segments:
        try:
            key = key_fn(seg)
        except Exception:
            continue
        if key is not None and key in old_key_map:
            setattr(seg, id_attr, old_key_map[key])

def compare_segments(seg1, seg2, attrs=('wire_id','start_node','end_node','twisted')):
    """
    Compare two segment objects for equality of specified attributes.
    Args:
        seg1: First segment object.
        seg2: Second segment object.
        attrs (tuple): Attributes to compare.
    Returns:
        bool: True if all attributes match, False otherwise.
    """
    return all(getattr(seg1, a) == getattr(seg2, a) for a in attrs)

def set_uuid_generator_for_test(fn: Callable[[], str]):
    """
    Set a custom UUID generator function for testing purposes.
    Args:
        fn (callable): Function that returns a UUID string.
    """
    global _uuid_generator
    _uuid_generator = fn

def reset_uuid_generator():
    """
    Reset the UUID generator to the default uuid4-based generator.
    """
    global _uuid_generator
    _uuid_generator = lambda: str(uuid.uuid4())
