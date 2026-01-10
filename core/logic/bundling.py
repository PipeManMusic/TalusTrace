import math
from typing import List, Tuple, Any, Dict, Optional
from core.geometry import SpatialHasher
from .base import iter_segments

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

# Minimal create_twisted_pair for test
class DummyTwistedPair:
    def __init__(self, wires):
        self.wires = wires

def create_twisted_pair(harness, wire_ids):
    tp = DummyTwistedPair(wires=wire_ids)
    if not hasattr(harness, 'twisted_pairs'):
        harness.twisted_pairs = []
    harness.twisted_pairs.append(tp)
    return tp

# PH2-2.2: BundleEngine for automatic bundle grouping
class BundleSegment:
    def __init__(self, wire_ids: List[str], segment_key: Tuple):
        self.wire_ids = wire_ids
        self.segment_key = segment_key

class BundleEngine:
    def __init__(self, grid_size: float = 2.0):
        self.hasher = SpatialHasher(grid_size=grid_size)

    def compute_bundles(self, wires: List[Any]) -> List[BundleSegment]:
        """
        Groups wires sharing a spatial hash into BundleSegments.
        """
        segment_map = {}
        for wire in wires:
            nodes = getattr(wire, 'path_nodes', [])
            
            # Use shared iterator from base.py
            for seg in iter_segments(nodes):
                key = self.hasher.get_key(seg)
                if key not in segment_map:
                    segment_map[key] = set()
                segment_map[key].add(wire.id)
        
        bundles = []
        for key, wire_ids in segment_map.items():
            if len(wire_ids) > 1:
                bundles.append(BundleSegment(list(wire_ids), key))
        return bundles