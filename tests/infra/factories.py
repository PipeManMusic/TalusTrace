"""
Test data factories for bundles, wires, and related models.
Generates valid, complex, and nested/twisted cases for use in infra tests.
"""
from core.bundle import Bundle, BundleSegmentMembership
from core.wire import Wire, WireSegment
from core.device import Device
from core.pin import Pin
from core.harness import Harness
from core.enums import Side
import uuid


def make_wire(
    from_conn="A", from_pin="1", to_conn="B", to_pin="2", twisted=False, segment_memberships=None, **kwargs
):
    seg = WireSegment(
        id=str(uuid.uuid4()),
        start_node=0,
        end_node=1,
        meta={},
    )
    wire = Wire(
        id=str(uuid.uuid4()),
        from_conn=from_conn,
        from_pin=from_pin,
        to_conn=to_conn,
        to_pin=to_pin,
        segments=[seg],
        twisted=twisted,
        segment_memberships=segment_memberships or [],
        **kwargs
    )
    return wire


def make_bundle(
    wire_ids=None, bundle_ids=None, segments=None, meta=None, id=None
):
    bundle = Bundle(
        wire_ids=wire_ids or [],
        bundle_ids=bundle_ids or [],
        segments=segments or [],
        meta=meta or {},
        id=id,
    )
    return bundle


def make_nested_bundle(depth=2, wires_per_level=2, twisted=False):
    """Create a nested bundle structure for testing."""
    bundles = []
    parent = None
    for d in range(depth):
        wires = [make_wire(twisted=twisted) for _ in range(wires_per_level)]
        b = make_bundle(name=f"B{d+1}", wires=wires, twisted=twisted)
        if parent:
            b.children.append(parent)
        parent = b
        bundles.append(b)
    return parent


def make_twisted_bundle(wire_count=2):
    wires = [make_wire(twisted=True) for _ in range(wire_count)]
    bundle = make_bundle(name="Twisted", wires=wires, twisted=True)
    return bundle


def make_harness_with_bundles(bundle_count=2, wires_per_bundle=2, nested=False, twisted=False):
    bundles = []
    for i in range(bundle_count):
        if nested:
            b = make_nested_bundle(depth=2, wires_per_level=wires_per_bundle, twisted=twisted)
        else:
            wires = [make_wire(twisted=twisted) for _ in range(wires_per_bundle)]
            b = make_bundle(name=f"B{i+1}", wires=wires, twisted=twisted)
        bundles.append(b)
    harness = Harness(
        id=str(uuid.uuid4()),
        bundles=bundles,
        devices=[],
        pins=[],
        meta={},
    )
    return harness


def make_segment_membership(wire_id, start_node=0, end_node=1, twisted=False, meta=None, id=None):
    return BundleSegmentMembership(
        wire_id=wire_id,
        start_node=start_node,
        end_node=end_node,
        twisted=twisted,
        meta=meta or {},
        id=id,
    )
