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
import math
from typing import List, Tuple, Optional, Dict, Any
from core.geometry import SpatialHasher

# PH3-1.2: Core: Implement Packing Factor Calculation
def calculate_bundle_diameter(wire_diameters: List[float]) -> float:
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
            for i in range(len(nodes) - 1):
                seg = (nodes[i], nodes[i+1])
                key = self.hasher.get_key(seg)
                if key not in segment_map:
                    segment_map[key] = set()
                segment_map[key].add(wire.id)
        
        bundles = []
        for key, wire_ids in segment_map.items():
            if len(wire_ids) > 1:
                bundles.append(BundleSegment(list(wire_ids), key))
        return bundles

# PH2-3.2: Core: Calculate Label MM Position from T-Pos
def calculate_label_mm_position(nodes: List[Tuple[float, float]], t: float) -> Tuple[float, float]:
    """
    Interpolates the mm position along a multi-segment wire (Spec 5).
    """
    if not nodes or len(nodes) < 2:
        raise ValueError("Wire must have at least two nodes")
    
    segments = [(nodes[i], nodes[i+1]) for i in range(len(nodes)-1)]
    lengths = [math.hypot(b[0]-a[0], b[1]-a[1]) for a, b in segments]
    total_length = sum(lengths)
    
    if total_length == 0:
        return nodes[0]
    
    target_length = t * total_length
    acc = 0.0
    for idx, seg_len in enumerate(lengths):
        if acc + seg_len >= target_length:
            a, b = segments[idx]
            seg_t = (target_length - acc) / seg_len if seg_len > 0 else 0.0
            x = a[0] + (b[0] - a[0]) * seg_t
            y = a[1] + (b[1] - a[1]) * seg_t
            return (x, y)
        acc += seg_len
    return nodes[-1]

# PH3-3.1: Engineering Rule for Bundle Stiffness
def check_bundle_constraints(wire_diameters: List[float]) -> Optional[Dict[str, Any]]:
    """
    Core engineering rule for bundle stiffness (Spec 7).
    Standard Rule: Bundles > 40mm are too stiff for Bronco II routing.
    """
    diameter = calculate_bundle_diameter(wire_diameters)
    if diameter > 40.0:
        return {
            "category": "STIFFNESS",
            "severity": "WARNING",
            "value": diameter,
            "message": f"Bundle diameter ({diameter:.2f}mm) exceeds 40mm flexible limit."
        }
    return None

def check_bend_radius_violations(path_nodes, wire_diameter, min_bend_factor=4.0):
    """
    Checks each wire segment for bend radius violations.
    Returns None if compliant, or a dict with details if violations found.
    path_nodes: List of (x, y) mm tuples
    wire_diameter: Diameter in mm
    min_bend_factor: Minimum allowed bend radius as a multiple of diameter (default 4x)
    """
    min_radius = wire_diameter * min_bend_factor
    violations = []
    # Check each corner (excluding endpoints)
    for i in range(1, len(path_nodes) - 1):
        p0, p1, p2 = path_nodes[i-1], path_nodes[i], path_nodes[i+1]
        v1 = (p0[0] - p1[0], p0[1] - p1[1])
        v2 = (p2[0] - p1[0], p2[1] - p1[1])
        dot = v1[0]*v2[0] + v1[1]*v2[1]
        mag1 = math.hypot(*v1)
        mag2 = math.hypot(*v2)
        if mag1 == 0 or mag2 == 0:
            continue
        cos_theta = dot / (mag1 * mag2)
        cos_theta = max(-1.0, min(1.0, cos_theta))
        theta = math.acos(cos_theta)
        if theta == 0:
            continue
        radius = mag1 / math.tan(theta / 2)
        if radius < min_radius:
            violations.append(i)
    if violations:
        return {
            "category": "BEND_RADIUS",
            "severity": "ERROR",
            "indices": violations
        }
    return None