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