"""
Bundling logic for Talus Trace.
Implements bundle group creation and bundle engine classes.
"""

import math
from typing import List, Tuple, Any, Dict, Optional
from core.geometry import SpatialHasher
from .base import iter_segments
from core.bundle import Bundle, BundleSegmentMembership

# PH3-1.2: Core: Implement Packing Factor Calculation
def calculate_bundle_diameter(wire_diameters: List[Any]) -> float:
    """
    Calculates bundle diameter using the industrial formula (Spec 2.2):
    D = 1.15 * sqrt(sum d^2).
    Supports shielded wires as dicts: {"diameter": x, "shield_thickness": y}
    """
    if not wire_diameters:
        return 0.0
    effective_diameters = []
    for d in wire_diameters:
        if isinstance(d, dict):
            # Shielded wire: diameter + 2*shield_thickness
            effective_diameters.append(d["diameter"] + 2 * d.get("shield_thickness", 0))
        else:
            effective_diameters.append(d)
    return 1.15 * (sum(dd**2 for dd in effective_diameters) ** 0.5)

# PH5-WIRE.2: Create Bundle Grouping
def create_bundle_group(harness, wires):
    """
    Create a group of bundles for wire organization.
    Returns:
        BundleGroup: The created bundle group.
    """
    # Generate a unique bundle ID (e.g., BUNDLE-1, BUNDLE-2, ...)
    if not hasattr(harness, '_bundle_counter'):
        harness._bundle_counter = 1
    bundle_id = f"BUNDLE-{harness._bundle_counter}"
    harness._bundle_counter += 1
    for wire in wires:
        if not hasattr(wire, 'meta') or wire.meta is None:
            wire.meta = {}
        wire.meta['bundle_group'] = bundle_id
    return bundle_id

# New: Create a twisted bundle (helix) using the new Bundle model
def create_twisted_bundle(wires, start_node=0, end_node=1, meta=None):
    """
    Create a twisted bundle (helix) from a list of wires.
    Each wire segment is marked as twisted.
    Returns a Bundle instance with proper segment memberships.
    """
    if meta is None:
        meta = {}
    segments = []
    for w in wires:
        seg = BundleSegmentMembership(
            wire_id=w.id,
            start_node=start_node,
            end_node=end_node,
            twisted=True
        )
        segments.append(seg)
    bundle = Bundle(
        wire_ids=[w.id for w in wires],
        segments=segments,
        meta=meta
    )
    return bundle

# PH2-2.2: BundleEngine for automatic bundle grouping
class BundleSegment:
    """
    Represents a segment within a wire bundle.
    """
    def __init__(self, wire_ids: List[str], segment_key: Tuple):
        """
        Initialize a bundle segment with endpoints and properties.
        """
        self.wire_ids = wire_ids
        self.segment_key = segment_key

class BundleEngine:
    """
    Engine for managing and optimizing wire bundles.
    """
    def __init__(self, grid_size: float = 2.0):
        """
        Initialize the bundle engine for wire management.
        """
        self.hasher = SpatialHasher(grid_size=grid_size)

    def compute_bundles(self, wires: List[Any]) -> List[Bundle]:
        """
        Groups wires sharing a spatial hash into Bundle objects with segment memberships.
        """
        segment_map = {}
        for wire in wires:
            nodes = getattr(wire, 'path_nodes', [])
            for seg in iter_segments(nodes):
                key = self.hasher.get_key(seg)
                if key not in segment_map:
                    segment_map[key] = set()
                segment_map[key].add(wire.id)
        bundles = []
        for key, wire_ids in segment_map.items():
            if len(wire_ids) > 1:
                segments = [
                    BundleSegmentMembership(
                        wire_id=wid,
                        start_node=key[0],
                        end_node=key[1],
                        twisted=True
                    ) for wid in wire_ids
                ]
                bundle = Bundle(
                    wire_ids=list(wire_ids),
                    segments=segments,
                    meta={"auto": True, "segment_key": key}
                )
                bundles.append(bundle)
        return bundles