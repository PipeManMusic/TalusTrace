
"""
Bundle and segment logic for Talus Trace core.
Implements bundle, segment, and membership validation and event stubs.
"""
import uuid

# Local implementation to avoid infra import
def restore_uuids_by_key(new_segments, old_segments, key_fn, id_attr='id'):
    """Restore UUIDs for segments by key."""
    """
    For each segment in new_segments, if its key matches one in old_segments, restore its UUID.
    """
    old_key_map = {}
    for s in old_segments:
        try:
            k = key_fn(s)
        except Exception:
            continue
        if k is not None:
            old_key_map[k] = getattr(s, id_attr, None)
    for seg in new_segments:
        try:
            k = key_fn(seg)
        except Exception:
            continue
        if k in old_key_map and old_key_map[k] is not None:
            setattr(seg, id_attr, old_key_map[k])

def ensure_unique_uuids(segments, id_attr='id'):
    """Ensure all segments have unique UUIDs."""
    """
    Ensures all segments have unique UUIDs for the given id_attr.
    """
    seen = set()
    for seg in segments:
        seg_id = getattr(seg, id_attr, None)
        if seg_id in seen or seg_id is None:
            setattr(seg, id_attr, str(uuid.uuid4()))
        seen.add(getattr(seg, id_attr))

 # Stub for on_bundle_merge to avoid NameError
class on_bundle_merge:
    """Event hook for bundle merge operations."""
    @staticmethod
    def fire(*args, **kwargs):
        """Fire the bundle merge event."""
        pass
from typing import List, Dict, Any, Optional

from dataclasses import dataclass, field
# Stub for on_bundle_split to avoid NameError
class on_bundle_split:
    """Event hook for bundle split operations."""
    @staticmethod
    def fire(*args, **kwargs):
        """Fire the bundle split event."""
        pass

from pydantic import ConfigDict



@dataclass
class BundleSegmentMembership:
    """
    Represents a wire segment's membership in a bundle, including nodes, twist status, and metadata.
    """
    wire_id: str
    start_node: int
    end_node: int
    twisted: bool = False  # True if this segment is twisted
    meta: Dict[str, Any] = field(default_factory=dict)
    id: Optional[str] = None

    def __post_init__(self):
        """
        Initialize the segment membership, generating a UUID if not provided.
        """
        if self.id is None:
            self.id = str(uuid.uuid4())

    def validate_membership(self):
        """
        Validate the integrity of the segment membership fields.
        Raises AssertionError if any field is invalid.
        """
        assert self.id is not None and isinstance(self.id, str), "Segment must have a valid UUID string."
        assert self.wire_id is not None and isinstance(self.wire_id, str), "Segment must have a valid wire_id."
        assert isinstance(self.start_node, int) and self.start_node >= 0, "start_node must be a non-negative int."
        assert isinstance(self.end_node, int) and self.end_node >= 0, "end_node must be a non-negative int."
        assert self.end_node > self.start_node, "end_node must be greater than start_node."
        assert isinstance(self.meta, dict), "meta must be a dict."

    def to_dict(self):
        """
        Serialize the segment membership to a dictionary.
        Returns:
            dict: Dictionary representation of the segment membership.
        """
        return {
            'wire_id': self.wire_id,
            'start_node': self.start_node,
            'end_node': self.end_node,
            'twisted': self.twisted,
            'meta': self.meta,
            'id': self.id
        }

    @classmethod
    def from_dict(cls, data):
        """
        Create a BundleSegmentMembership instance from a dictionary.
        Args:
            data (dict): Dictionary containing segment membership fields.
        Returns:
            BundleSegmentMembership: Instance created from the dictionary.
        """
        return cls(
            wire_id=data.get('wire_id'),
            start_node=data.get('start_node'),
            end_node=data.get('end_node'),
            twisted=data.get('twisted', False),
            meta=data.get('meta', {}),
            id=data.get('id')
        )



@dataclass
class Bundle:
    """
    Represents a bundle of wires and segments, supporting nested bundles and segment management.
    """
    wire_ids: List[str] = field(default_factory=list)
    bundle_ids: List[str] = field(default_factory=list)  # Nested bundles
    segments: List[BundleSegmentMembership] = field(default_factory=list)
    meta: Dict[str, Any] = field(default_factory=dict)
    id: Optional[str] = None

    def __post_init__(self):
        """
        Initialize the bundle, generating a UUID if not provided.
        """
        if self.id is None:
            self.id = str(uuid.uuid4())

    def get_segment_by_uuid(self, uuid: str):
        """
        Retrieve a segment from the bundle by its UUID.
        Args:
            uuid (str): UUID of the segment to retrieve.
        Returns:
            BundleSegmentMembership or None: The segment if found, else None.
        """
        for seg in self.segments:
            if seg.id == uuid:
                return seg
        return None

    def validate_segments(self):
        """
        Validate all segments in the bundle for integrity and correctness.
        Raises AssertionError if duplicate UUIDs or duplicate memberships are found.
        """
        seen_uuids = set()
        seen_keys = set()
        for seg in self.segments:
            seg.validate_membership()
            if seg.id in seen_uuids:
                raise AssertionError("Duplicate segment UUID detected!")
            seen_uuids.add(seg.id)
            key = (seg.wire_id, seg.start_node, seg.end_node, seg.twisted)
            if key in seen_keys:
                raise AssertionError("Duplicate segment membership detected!")
            seen_keys.add(key)
        # Optionally: check for valid wire_ids in self.wire_ids if available


    def to_dict(self):
        """
        Serialize the bundle to a dictionary.
        Returns:
            dict: Dictionary representation of the bundle.
        """
        return {
            'wire_ids': self.wire_ids,
            'bundle_ids': self.bundle_ids,
            'segments': [s.to_dict() for s in self.segments],
            'meta': self.meta,
            'id': self.id
        }

    @classmethod
    def from_dict(cls, data):
        """
        Create a Bundle instance from a dictionary.
        Args:
            data (dict): Dictionary containing bundle fields.
        Returns:
            Bundle: Instance created from the dictionary.
        """
        segments = [BundleSegmentMembership.from_dict(s) for s in data.get('segments', [])]
        return cls(
            wire_ids=data.get('wire_ids', []),
            bundle_ids=data.get('bundle_ids', []),
            segments=segments,
            meta=data.get('meta', {}),
            id=data.get('id')
        )
        """
        Validate all segments in this bundle for uniqueness and membership integrity.
        Checks: All segment UUIDs are unique, all memberships are valid, no duplicate (wire_id, start_node, end_node).
        """
        seen_uuids = set()
        seen_keys = set()
        for seg in self.segments:
            seg.validate_membership()
            assert seg.id not in seen_uuids, f"Duplicate segment UUID: {seg.id}"
            seen_uuids.add(seg.id)
            key = (seg.wire_id, seg.start_node, seg.end_node)
            assert key not in seen_keys, f"Duplicate segment membership: {key}"
            seen_keys.add(key)
        # Optionally: check for valid wire_ids in self.wire_ids if available


    def split_segment(self, segment_index: int, new_start: int, new_end: int):
        """
        Split the segment at segment_index by creating two new segments (with new_start/new_end indices).
        Only the two new segments adjacent to the split get new UUIDs; all other segments retain their UUIDs, matched by (wire_id, start_node, end_node).
        """
        old_segments = list(self.segments)
        old_keys = [(s.wire_id, s.start_node, s.end_node) for s in self.segments]
        if 0 <= segment_index < len(self.segments):
            seg = self.segments[segment_index]
            self.segments.pop(segment_index)
            left = BundleSegmentMembership(wire_id=seg.wire_id, start_node=seg.start_node, end_node=new_start, twisted=seg.twisted)
            right = BundleSegmentMembership(wire_id=seg.wire_id, start_node=new_start, end_node=seg.end_node, twisted=seg.twisted)
            self.segments.insert(segment_index, right)
            self.segments.insert(segment_index, left)
        restore_uuids_by_key(self.segments, old_segments, lambda s: (s.wire_id, s.start_node, s.end_node))
        ensure_unique_uuids(self.segments)
        on_bundle_split.fire(self, segment_index, new_start, new_end)

    def merge_segments(self, left_index: int):
        """
        Merge the segments at left_index and left_index+1 into a single segment.
        The resulting merged segment always gets a new UUID. All other unchanged segments (by key) restore their UUIDs.
        """
        old_segments = list(self.segments)
        old_keys = [(s.wire_id, s.start_node, s.end_node) for s in self.segments]
        if 0 <= left_index < len(self.segments) - 1:
            left = self.segments[left_index]
            right = self.segments[left_index + 1]
            merged = BundleSegmentMembership(wire_id=left.wire_id, start_node=left.start_node, end_node=right.end_node, twisted=left.twisted or right.twisted)
            self.segments.pop(left_index + 1)
            self.segments[left_index] = merged
        restore_uuids_by_key(self.segments, old_segments, lambda s: (s.wire_id, s.start_node, s.end_node))
        ensure_unique_uuids(self.segments)
        on_bundle_merge.fire(self, left_index)
