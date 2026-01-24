"""
infra/test_factories.py

Factory methods for generating test bundles and wires, including nested and twisted cases.
"""
from core.bundle import Bundle, BundleSegmentMembership
from core.wire import Wire, WireSegment
import random

def make_wire(from_conn="A", to_conn="B", n_segments=1):
    """
    Create a Wire object for testing with specified connections and number of segments.
    Args:
        from_conn (str): Starting connection name.
        to_conn (str): Ending connection name.
        n_segments (int): Number of wire segments to create.
    Returns:
        Wire: The created Wire object.
    """
    w = Wire(from_conn=from_conn, to_conn=to_conn)
    w.segments = [WireSegment(wire_id=w.id, start_node=i, end_node=i+1) for i in range(n_segments)]
    return w

def make_bundle(wire_ids=None, n_segments=1, twisted=False, meta=None):
    """
    Create a Bundle object for testing with specified wire IDs, segments, and metadata.
    Args:
        wire_ids (list): List of wire IDs for the bundle.
        n_segments (int): Number of bundle segments to create.
        twisted (bool): Whether segments are twisted.
        meta (dict): Optional metadata for the bundle.
    Returns:
        Bundle: The created Bundle object.
    """
    if wire_ids is None:
        wire_ids = [f"wire-{random.randint(1000,9999)}"]
    segs = [BundleSegmentMembership(wire_id=wire_ids[0], start_node=i, end_node=i+1, twisted=twisted) for i in range(n_segments)]
    return Bundle(wire_ids=wire_ids, segments=segs, meta=meta or {})

def make_nested_bundle(depth=2, width=2):
    """
    Create a nested bundle structure of given depth and width.
    """
    bundles = []
    for d in range(depth):
        wire_ids = [f"wire-{d}-{i}" for i in range(width)]
        b = make_bundle(wire_ids=wire_ids, n_segments=width)
        bundles.append(b)
    # Nest them
    for i in range(1, len(bundles)):
        bundles[i].bundle_ids = [bundles[i-1].id]
    return bundles[-1]
