# PH3-1.2: Core: Implement Packing Factor Calculation
def calculate_packing_diameter(wire_diameters):
    """
    Calculates bundle diameter using D = 1.15 * sqrt(sum d^2).
    wire_diameters: list of float diameters (mm)
    Returns float diameter (mm)
    """
    if not wire_diameters:
        return 0.0
    return 1.15 * (sum(d**2 for d in wire_diameters) ** 0.5)
from core.geometry import SpatialHasher

# PH2-2.2: BundleEngine for automatic bundle grouping
class BundleSegment:
    def __init__(self, wire_ids, segment_key):
        self.wire_ids = wire_ids
        self.segment_key = segment_key


class BundleEngine:
    def __init__(self, grid_size=2.0):
        self.hasher = SpatialHasher(grid_size=grid_size)

    def compute_bundles(self, wires):
        """
        Groups wires sharing a spatial hash into BundleSegments.
        Returns a list of BundleSegment objects.
        """
        segment_map = {}
        for wire in wires:
            nodes = getattr(wire, 'path_nodes', [])
            # For each segment in wire
            for i in range(len(nodes) - 1):
                seg = (nodes[i], nodes[i+1])
                key = self.hasher.get_key(seg)
                if key not in segment_map:
                    segment_map[key] = set()
                segment_map[key].add(wire.id)
        # Create BundleSegments for segments with >1 wire
        bundles = []
        for key, wire_ids in segment_map.items():
            if len(wire_ids) > 1:
                bundles.append(BundleSegment(list(wire_ids), key))
        return bundles


# PH2-3.2: Core: Calculate Label MM Position from T-Pos
def calculate_label_mm_position(nodes, t):
    """
    Interpolates the mm position along a multi-segment wire for a given t (0.0-1.0).
    nodes: List of (x, y) mm tuples
    t: float, 0.0=start, 1.0=end
    Returns (x, y) mm tuple
    """
    if not nodes or len(nodes) < 2:
        raise ValueError("Wire must have at least two nodes")
    # Calculate total length
    segments = [(nodes[i], nodes[i+1]) for i in range(len(nodes)-1)]
    lengths = []
    for a, b in segments:
        dx = b[0] - a[0]
        dy = b[1] - a[1]
        lengths.append((dx**2 + dy**2) ** 0.5)
    total_length = sum(lengths)
    if total_length == 0:
        return nodes[0]
    target_length = t * total_length
    # Walk segments to find where target_length falls
    acc = 0.0
    for idx, seg_len in enumerate(lengths):
        if acc + seg_len >= target_length:
            a, b = segments[idx]
            seg_t = (target_length - acc) / seg_len if seg_len > 0 else 0.0
            x = a[0] + (b[0] - a[0]) * seg_t
            y = a[1] + (b[1] - a[1]) * seg_t
            return (x, y)
        acc += seg_len
    # If t==1.0, return last node
    return nodes[-1]