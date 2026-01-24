"""
Wire module for Talus Trace.
Defines wire segments, labels, and wire models, including serialization and validation utilities.
"""
import uuid

# Local stubs for event hooks

from typing import List, Optional, Dict, Any, Literal
from dataclasses import dataclass, field
from core.bundle import BundleSegmentMembership



@dataclass
class WireSegment:
    """
    Represents a segment of a wire between two nodes, with metadata and unique ID.
    """
    start_node: int
    end_node: int
    meta: Dict[str, Any] = field(default_factory=dict)
    id: str = None

    def __post_init__(self):
        """
        Initialize WireSegment and assign a UUID if not provided.
        """
        if self.id is None:
            self.id = str(uuid.uuid4())

    def to_dict(self):
        """
        Serialize the WireSegment to a dictionary.
        Returns:
            dict: Dictionary representation of the WireSegment.
        """
        return {
            'start_node': self.start_node,
            'end_node': self.end_node,
            'meta': self.meta,
            'id': self.id
        }
    @classmethod
    def from_dict(cls, data):
        """
        Create a WireSegment instance from a dictionary.
        Args:
            data (dict): Dictionary with segment data.
        Returns:
            WireSegment: New instance.
        """
        return cls(
            start_node=data.get('start_node'),
            end_node=data.get('end_node'),
            meta=data.get('meta', {}),
            id=data.get('id')
        )




@dataclass
class WireLabel:
    """
    Represents a label attached to a wire, with text and position.
    """
    text: str
    t_pos: float = 0.5

    def to_dict(self):
        """
        Serialize the WireLabel to a dictionary.
        Returns:
            dict: Dictionary representation of the WireLabel.
        """
        return {
            'text': self.text,
            't_pos': self.t_pos
        }

    @classmethod
    def from_dict(cls, data):
        """
        Create a WireLabel instance from a dictionary.
        Args:
            data (dict): Dictionary with label data.
        Returns:
            WireLabel: New instance.
        """
        return cls(
            text=data.get('text'),
            t_pos=data.get('t_pos', 0.5)
        )



@dataclass
class Wire:
    """
    Represents a wire connecting two devices or pins, with segments, labels, and physical/logical properties.
    """
    # --- Identification ---
    id: str = None

    # --- Connectivity ---
    from_conn: str = ""
    from_pin: str = ""
    to_conn: str = ""
    to_pin: str = ""

    # --- Physical Properties ---
    color: str = "#808080"  # Hex color for rendering
    color_code: Optional[str] = None  # e.g., "RED/WHT" for spec compliance
    segments: List[WireSegment] = field(default_factory=list)
    labels: List[WireLabel] = field(default_factory=list)
    meta: Dict[str, Any] = field(default_factory=dict)
    gauge: Optional[str] = None
    type: Literal["STANDARD", "TWISTED_PAIR"] = "STANDARD"
    diameter_mm: float = 1.0
    length_mm: float = 0.0
    standard_id: Optional[str] = None
    z_index: int = 0
    twisted: bool = False
    pair_id: Optional[str] = None
    status: str = "UNDEFINED"  # Draft-First default
    signal_name: Optional[str] = None  # Logical signal carried

    @classmethod
    def from_dict(cls, data):
        """
        Create a Wire instance from a dictionary, including segments, labels, and memberships.
        Args:
            data (dict): Dictionary with wire data.
        Returns:
            Wire: New instance.
        """
        segments = [WireSegment.from_dict(s) for s in data.get('segments', [])]
        labels = [WireLabel.from_dict(l) for l in data.get('labels', [])]
        from core.bundle import BundleSegmentMembership
        segment_memberships = [BundleSegmentMembership.from_dict(s) for s in data.get('segment_memberships', [])]
        return cls(
            id=data.get('id'),
            from_conn=data.get('from_conn', ""),
            from_pin=data.get('from_pin', ""),
            to_conn=data.get('to_conn', ""),
            to_pin=data.get('to_pin', ""),
            color=data.get('color', "#808080"),
            color_code=data.get('color_code'),
            segments=segments,
            labels=labels,
            meta=data.get('meta', {}),
            gauge=data.get('gauge'),
            type=data.get('type', "STANDARD"),
            diameter_mm=data.get('diameter_mm', 1.0),
            length_mm=data.get('length_mm', 0.0),
            standard_id=data.get('standard_id'),
            z_index=data.get('z_index', 0),
            twisted=data.get('twisted', False),
            pair_id=data.get('pair_id'),
            status=data.get('status', "UNDEFINED"),
            signal_name=data.get('signal_name'),
            segment_memberships=segment_memberships,
            path_nodes=data.get('path_nodes', []),
        )

    def __post_init__(self):
        """
        Initialize Wire and assign a UUID if not provided. Validates UUID format.
        """
        if self.id is None:
            self.id = str(uuid.uuid4())
        elif not is_valid_uuid(self.id):
            raise ValueError(f"Wire id must be a valid UUID, got: {self.id}")

    def to_dict(self):
        """
        Serialize the Wire to a dictionary, including segments, labels, and memberships.
        Returns:
            dict: Dictionary representation of the Wire.
        """
        d = {
            'id': self.id,
            'from_conn': self.from_conn,
            'from_pin': self.from_pin,
            'to_conn': self.to_conn,
            'to_pin': self.to_pin,
            'color': self.color,
            'color_code': self.color_code,
            'segments': [s.to_dict() for s in self.segments],
            'labels': [l.to_dict() for l in self.labels],
            'meta': self.meta,
            'gauge': self.gauge,
            'type': self.type,
            'diameter_mm': self.diameter_mm,
            'length_mm': self.length_mm,
            'standard_id': self.standard_id,
            'z_index': self.z_index,
            'twisted': self.twisted,
            'pair_id': self.pair_id,
            'status': self.status,
            'signal_name': self.signal_name,
            'segment_memberships': [s.to_dict() for s in self.segment_memberships],
            'path_nodes': self.path_nodes
        }
        on_wire_serialize.fire(self, d)
        return d



    # --- Geometry (MM) ---
    path_nodes: List[List[float]] = field(default_factory=list)  # Polyline in mm

    # --- Segments ---
    # segments already defined above with dataclasses.field

    # --- Segment Memberships ---
    segment_memberships: List[BundleSegmentMembership] = field(default_factory=list)

    def update_segments(self):
        """
        Update the wire's segments based on the current path_nodes.
        Preserves UUIDs for unchanged segments and assigns new UUIDs for splits.
        """
        def node_tuple(node):
            """
            Convert a node to a tuple for segment mapping.
            Args:
                node (list or tuple): Node coordinates.
            Returns:
                tuple: Node as a tuple.
            """
            return tuple(node) if isinstance(node, (list, tuple)) else (node,)
        # Build a map from (start_coord, end_coord) to segment for old segments
        old_segments = {}
        for seg in getattr(self, 'segments', []):
            try:
                start_coord = node_tuple(self.path_nodes[seg.start_node])
                end_coord = node_tuple(self.path_nodes[seg.end_node])
                old_segments[(start_coord, end_coord)] = seg
            except Exception:
                continue
        # Detect splits: if a segment in old_segments is not present in the new path, it was split
        old_keys = set(old_segments.keys())
        new_keys = set()
        for i in range(len(self.path_nodes) - 1):
            start_coord = node_tuple(self.path_nodes[i])
            end_coord = node_tuple(self.path_nodes[i+1])
            new_keys.add((start_coord, end_coord))
        split_keys = old_keys - new_keys
        # Any new segment that shares an endpoint with a split segment should get a new UUID
        split_endpoints = set()
        for k in split_keys:
            split_endpoints.update(k)
        new_segments = []
        for i in range(len(self.path_nodes) - 1):
            start_coord = node_tuple(self.path_nodes[i])
            end_coord = node_tuple(self.path_nodes[i+1])
            key = (start_coord, end_coord)
            # Only preserve UUID if this segment existed before, is not part of a split, and endpoints are not shared with a split
            if (
                key in old_segments
                and start_coord not in split_endpoints
                and end_coord not in split_endpoints
            ):
                seg = old_segments[key]
                seg.start_node = i
                seg.end_node = i+1
            else:
                seg = WireSegment(start_node=i, end_node=i+1)
            new_segments.append(seg)
        self.segments = new_segments

    def split_segment(self, segment_uuid: str, new_node: list):
        """
        Split the segment with the given UUID by inserting new_node into path_nodes.
        Returns the UUIDs of the two new segments. All lookups and mutations are by UUID.
        """
        # Find the segment by UUID
        segment = next((s for s in self.segments if s.id == segment_uuid), None)
        if segment is None:
            raise ValueError(f"Segment UUID {segment_uuid} not found")
        # Save original start/end node coordinates
        start_coord = self.path_nodes[segment.start_node]
        end_coord = self.path_nodes[segment.end_node]
        insert_at = segment.end_node
        old_segments = list(self.segments)
        self.path_nodes.insert(insert_at, new_node)
        self.update_segments()
        # Find the two new segments by matching coordinates
        left_seg = next((s for s in self.segments if self.path_nodes[s.start_node] == start_coord and self.path_nodes[s.end_node] == new_node), None)
        right_seg = next((s for s in self.segments if self.path_nodes[s.start_node] == new_node and self.path_nodes[s.end_node] == end_coord), None)
        if not left_seg or not right_seg:
            raise RuntimeError("Could not identify new split segments by UUID")
        # Local stubs for restore_uuids_by_key, ensure_unique_uuids (infra import removed)
        def restore_uuids_by_key(*args, **kwargs):
            """Restore UUIDs for segments by key (stub)."""
            pass
        def ensure_unique_uuids(*args, **kwargs):
            """Ensure all segments have unique UUIDs (stub)."""
            pass
        def key_fn(segment):
            """
            Generate a key for segment mapping based on endpoints.
            Args:
                segment (WireSegment): Segment to generate key for.
            Returns:
                tuple: Key representing segment endpoints.
            """
            try:
                return (
                    tuple(self.path_nodes[segment.start_node]),
                    tuple(self.path_nodes[segment.end_node])
                )
            except IndexError:
                return None
        # Filter out old segments whose indices are now invalid
        valid_old_segments = [s for s in old_segments if key_fn(s) is not None]
        restore_uuids_by_key(self.segments, valid_old_segments, key_fn)
        seen = set()
        for i, seg in enumerate(self.segments):
            if seg.id in seen:
                self.segments[i] = type(seg)(start_node=seg.start_node, end_node=seg.end_node)
            seen.add(self.segments[i].id)
        ensure_unique_uuids(self.segments)
        # Fire event hook for split (pass UUIDs)
        new_uuids = (left_seg.id, right_seg.id)
        on_wire_split.fire(self, segment_uuid, new_node, new_uuids)
        return new_uuids

    def merge_segments(self, left_segment_uuid: str):
        """
        Merge the segment with the given UUID and the next segment (by UUID).
        The resulting merged segment always gets a new UUID. All lookups and mutations are by UUID. Returns the new merged segment UUID.
        """
        left = next((s for s in self.segments if s.id == left_segment_uuid), None)
        if left is None:
            raise ValueError(f"Segment UUID {left_segment_uuid} not found")
        # Find the right segment (must be adjacent in path)
        right = next((s for s in self.segments if s.start_node == left.end_node), None)
        if right is None:
            raise ValueError(f"No adjacent segment to merge with for UUID {left_segment_uuid}")
        # Save original start/end node coordinates
        start_coord = self.path_nodes[left.start_node]
        end_coord = self.path_nodes[right.end_node]
        node_index = left.end_node
        if 0 < node_index < len(self.path_nodes) - 1:
            old_segments = list(self.segments)
            self.path_nodes.pop(node_index)
            self.update_segments()
            # Find the new merged segment by matching coordinates
            merged = next((s for s in self.segments if self.path_nodes[s.start_node] == start_coord and self.path_nodes[s.end_node] == end_coord), None)
            if merged is None:
                raise RuntimeError("Could not identify merged segment by UUID")
            # Local stubs for restore_uuids_by_key, ensure_unique_uuids (infra import removed)
            def restore_uuids_by_key(*args, **kwargs):
                """Restore UUIDs for segments by key (stub)."""
                pass
            def ensure_unique_uuids(*args, **kwargs):
                """Ensure all segments have unique UUIDs (stub)."""
                pass
            def key_fn(segment):
                """
                Generate a key for segment mapping based on endpoints.
                Args:
                    segment (WireSegment): Segment to generate key for.
                Returns:
                    tuple: Key representing segment endpoints.
                """
                try:
                    return (
                        tuple(self.path_nodes[segment.start_node]),
                        tuple(self.path_nodes[segment.end_node])
                    )
                except IndexError:
                    return None
            restore_uuids_by_key(self.segments, old_segments, key_fn)
            seen = set()
            for i, seg in enumerate(self.segments):
                if seg.id in seen:
                    self.segments[i] = type(seg)(start_node=seg.start_node, end_node=seg.end_node)
                seen.add(self.segments[i].id)
            ensure_unique_uuids(self.segments)
            # Fire event hook for merge (pass UUIDs)
            on_wire_merge.fire(self, left_segment_uuid, merged.id)
            return merged.id


    # --- Metadata ---
    labels: List[WireLabel] = field(default_factory=list)
    meta: Dict[str, Any] = field(default_factory=dict)

    # --- Spec Compliance & Promotion ---
    def promote_to_specified(self, standard_id: str, gauge: str, color_code: str, diameter_mm: float):
        """
        Promote wire from UNDEFINED to SPECIFIED, assigning standard, gauge, color, and diameter.
        Should be called by infra/api after user selection.
        """
        self.status = "SPECIFIED"
        self.standard_id = standard_id
        self.gauge = gauge
        self.color_code = color_code
        self.diameter_mm = diameter_mm
        # Optionally trigger audit/validation here or via infra/api

    def get_segment_by_id(self, segment_id: str):
        """
        Retrieve a wire segment by its unique ID.
        Args:
            segment_id (str): UUID of the segment to find.
        Returns:
            WireSegment or None: The segment if found, else None.
        """
        for seg in self.segments:
            if seg.id == segment_id:
                return seg
        return None

    @property
    def render_color(self) -> str:
        """
        Returns color for rendering: default theme color if UNDEFINED, else color_code or color.
        UI should use this property.
        """
        if self.status == "UNDEFINED":
            return self.meta.get("theme_wire_default", "#808080")
        return self.color_code if self.color_code else self.color

    @property
    def render_thickness(self) -> float:
        """
        Returns thickness for rendering: fixed in Diagram Mode, diameter_mm in Formboard Mode.
        UI should set mode and use this property.
        """
        mode = self.meta.get("render_mode", "diagram")
        if mode == "diagram":
            return 2.0  # px, example value
        return self.diameter_mm

    # --- Interaction Points for infra/api ---
    # - infra/api should handle grid snapping, inferred bundling, and audit triggers.
    # - core exposes geometry, status, and promote_to_specified for compliance.
class on_wire_split:
    """Event hook for wire split operations."""
    _subscribers = []
    @classmethod
    def subscribe(cls, callback):
        """Subscribe a callback to the wire split event."""
        cls._subscribers.append(callback)
    @classmethod
    def fire(cls, *args, **kwargs):
        """Fire the wire split event."""
        for cb in cls._subscribers:
            cb(*args, **kwargs)
    @classmethod
    def clear_subscribers(cls):
        """Clear all wire split event subscribers."""
        cls._subscribers.clear()
    @classmethod
    def unsubscribe(cls, callback):
        """Unsubscribe a callback from the wire split event."""
        if callback in cls._subscribers:
            cls._subscribers.remove(callback)

class on_wire_merge:
    """Event hook for wire merge operations."""
    _subscribers = []
    @classmethod
    def subscribe(cls, callback):
        """Subscribe a callback to the wire merge event."""
        cls._subscribers.append(callback)
    @classmethod
    def fire(cls, *args, **kwargs):
        """Fire the wire merge event."""
        for cb in cls._subscribers:
            cb(*args, **kwargs)
    @classmethod
    def clear_subscribers(cls):
        """Clear all wire merge event subscribers."""
        cls._subscribers.clear()
    @classmethod
    def unsubscribe(cls, callback):
        """Unsubscribe a callback from the wire merge event."""
        if callback in cls._subscribers:
            cls._subscribers.remove(callback)

class on_wire_serialize:
    """Event hook for wire serialization operations."""
    _subscribers = []
    @classmethod
    def subscribe(cls, callback):
        """Subscribe a callback to the wire serialize event."""
        cls._subscribers.append(callback)
    @classmethod
    def fire(cls, *args, **kwargs):
        """Fire the wire serialize event."""
        for cb in cls._subscribers:
            cb(*args, **kwargs)
    @classmethod
    def clear_subscribers(cls):
        """Clear all wire serialize event subscribers."""
        cls._subscribers.clear()
    @classmethod
    def unsubscribe(cls, callback):
        """Unsubscribe a callback from the wire serialize event."""
        if callback in cls._subscribers:
            cls._subscribers.remove(callback)
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