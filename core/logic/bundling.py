"""
Bundling logic for Talus Trace.
Implements bundle group creation and wire-overlap inference.
"""

from dataclasses import dataclass, field
from typing import List, Tuple, Any, Dict
import math
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

@dataclass
class OverlapGroup:
    """
    A group of wires that share a single coincident path segment (a 'common
    section') and are therefore candidates to be upgraded into a bundle.

    Attributes:
        key: Canonical grid key of the shared segment (from SpatialHasher).
        members: List of (wire_id, start_node, end_node) tuples — the segment
            indices *within each wire's own path_nodes* that lie on the shared
            section. Each wire appears at most once.
    """
    key: Any
    members: List[Tuple[str, int, int]] = field(default_factory=list)

    @property
    def wire_ids(self) -> List[str]:
        """Return the unique wire IDs participating in this overlap, in order."""
        return list(dict.fromkeys(wid for (wid, _s, _e) in self.members))


def _segment_key_signature(key) -> Any:
    """Normalize a spatial-hash key (possibly nested lists, from a loaded bundle)
    to a hashable, comparable form so keys survive serialization boundaries."""
    if isinstance(key, (list, tuple)):
        return tuple(_segment_key_signature(item) for item in key)
    return key


def _as_xy(pt) -> Tuple[float, float]:
    """Coerce a path node to a float (x, y) pair."""
    return float(pt[0]), float(pt[1])


def _segments_parallel_adjacent(a1, a2, b1, b2, tolerance: float, angle_tolerance: float) -> bool:
    """Return True if segment A (a1->a2) and B (b1->b2) run alongside each other.

    They coalesce when they are approximately parallel (angle within
    ``angle_tolerance`` radians), their perpendicular offset is within
    ``tolerance`` (≈ one grid cell), and their projections onto A's axis
    genuinely overlap (touching only at a point does not count).
    """
    ax1, ay1 = a1
    ax2, ay2 = a2
    bx1, by1 = b1
    bx2, by2 = b2
    dax, day = ax2 - ax1, ay2 - ay1
    dbx, dby = bx2 - bx1, by2 - by1
    la = (dax * dax + day * day) ** 0.5
    lb = (dbx * dbx + dby * dby) ** 0.5
    if la < 1e-9 or lb < 1e-9:
        return False
    ux, uy = dax / la, day / la
    # Parallelism: magnitude of the cross product of the unit directions.
    cross = (dax * dby - day * dbx) / (la * lb)
    if abs(cross) > math.sin(angle_tolerance):
        return False
    # Perpendicular distance of B's endpoints from A's infinite line (normal = (-uy, ux)).
    d1 = abs((bx1 - ax1) * (-uy) + (by1 - ay1) * ux)
    d2 = abs((bx2 - ax1) * (-uy) + (by2 - ay1) * ux)
    if d1 > tolerance or d2 > tolerance:
        return False
    # Projected overlap along A's axis (A spans [0, la]).
    tb1 = (bx1 - ax1) * ux + (by1 - ay1) * uy
    tb2 = (bx2 - ax1) * ux + (by2 - ay1) * uy
    lo = max(0.0, min(tb1, tb2))
    hi = min(la, max(tb1, tb2))
    return (hi - lo) > 1e-9


def find_wire_overlaps(
    wires,
    grid_size: float = 2.0,
    existing_bundles=None,
    tolerance: float = None,
    angle_tolerance: float = 0.17453293,
) -> List[OverlapGroup]:
    """
    Detect groups of wires that share a common run (hybrid grid + proximity).

    Wire segments coalesce when they run alongside each other: approximately
    parallel (within ``angle_tolerance`` radians), within ``tolerance`` mm
    perpendicular offset (defaults to one grid cell, ``grid_size``), and with a
    genuine projected overlap. This captures both exactly-coincident runs (the
    spec's grid-coordinate hashing) and near-parallel runs one grid cell apart.

    Args:
        wires: Iterable of Wire models (must expose ``id`` and ``path_nodes``).
        grid_size: Grid resolution in mm; also the canonical key resolution.
        existing_bundles: Optional iterable of Bundle models. Groups whose shared
            run is already covered by an existing bundle (matched via
            ``bundle.meta['segment_key']``) are excluded.
        tolerance: Perpendicular coalescence tolerance in mm. Defaults to
            ``grid_size`` (≈ one grid cell).
        angle_tolerance: Maximum angle (radians) between coalescing segments.

    Returns:
        List of :class:`OverlapGroup`, one per shared run involving two or more
        distinct wires.
    """
    if tolerance is None:
        tolerance = grid_size
    hasher = SpatialHasher(grid_size=grid_size)

    # Collect segment records: (wire_id, seg_idx, p1, p2).
    segs: List[Tuple[str, int, Tuple[float, float], Tuple[float, float]]] = []
    for wire in wires or []:
        wid = getattr(wire, 'id', None)
        if wid is None:
            continue
        nodes = getattr(wire, 'path_nodes', []) or []
        for idx, (p1, p2) in enumerate(iter_segments(nodes)):
            segs.append((wid, idx, _as_xy(p1), _as_xy(p2)))

    # Union-find over segment records, merging parallel-adjacent segments.
    parent = list(range(len(segs)))

    def _find(i: int) -> int:
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def _union(i: int, j: int) -> None:
        ri, rj = _find(i), _find(j)
        if ri != rj:
            parent[ri] = rj

    for i in range(len(segs)):
        _, _, a1, a2 = segs[i]
        for j in range(i + 1, len(segs)):
            if segs[i][0] == segs[j][0]:
                continue  # never coalesce a wire's own segments
            _, _, b1, b2 = segs[j]
            if _segments_parallel_adjacent(a1, a2, b1, b2, tolerance, angle_tolerance):
                _union(i, j)

    # Gather clusters. Preserve first-seen order for stable member selection.
    clusters: Dict[int, List[int]] = {}
    for i in range(len(segs)):
        clusters.setdefault(_find(i), []).append(i)

    already_bundled = set()
    for bundle in existing_bundles or []:
        meta = getattr(bundle, 'meta', None) or {}
        sk = meta.get('segment_key')
        if sk is not None:
            already_bundled.add(_segment_key_signature(sk))

    groups: List[OverlapGroup] = []
    for _root, seg_indices in clusters.items():
        # First segment per wire (input order) becomes that wire's membership.
        members: Dict[str, Tuple[int, int]] = {}
        for si in seg_indices:
            wid, idx, _p1, _p2 = segs[si]
            if wid not in members:
                members[wid] = (idx, idx + 1)
        if len(members) < 2:
            continue
        key = tuple(sorted(
            hasher.get_key((segs[si][2], segs[si][3])) for si in seg_indices
        ))
        if _segment_key_signature(key) in already_bundled:
            continue
        groups.append(OverlapGroup(
            key=key,
            members=[(wid, s, e) for wid, (s, e) in members.items()],
        ))
    return groups


def build_bundle_from_overlap(group: OverlapGroup) -> Bundle:
    """
    Construct a :class:`Bundle` from an :class:`OverlapGroup`.

    Each participating wire contributes one :class:`BundleSegmentMembership`
    recording the segment of that wire lying on the shared run. The canonical
    grid key is stored in ``meta['segment_key']`` (recursively as lists, for
    serialization) so future overlap scans can skip an already-bundled run.
    """
    segments = [
        BundleSegmentMembership(wire_id=wid, start_node=s, end_node=e)
        for (wid, s, e) in group.members
    ]
    return Bundle(
        wire_ids=group.wire_ids,
        segments=segments,
        meta={"auto": True, "segment_key": _key_to_serializable(group.key)},
    )


def _key_to_serializable(key) -> Any:
    """Recursively convert a grid key of nested tuples into nested lists."""
    if isinstance(key, (list, tuple)):
        return [_key_to_serializable(item) for item in key]
    return key
