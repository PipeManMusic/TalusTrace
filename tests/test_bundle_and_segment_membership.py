import uuid
from core.bundle import Bundle, BundleSegmentMembership
from core.wire import Wire

def test_bundle_creation_and_membership():
    # Create wires
    w1 = Wire(from_conn="A", to_conn="B")
    w2 = Wire(from_conn="C", to_conn="D")

    # Create segment memberships
    seg1 = BundleSegmentMembership(wire_id=w1.id, start_node=0, end_node=2)
    seg2 = BundleSegmentMembership(wire_id=w2.id, start_node=1, end_node=3)

    # Create bundle
    bundle = Bundle(
        wire_ids=[w1.id, w2.id],
        segments=[seg1, seg2],
        meta={"bundle_type": "main"}
    )

    # Bundle should have correct members
    assert w1.id in bundle.wire_ids
    assert w2.id in bundle.wire_ids
    assert bundle.meta["bundle_type"] == "main"
    assert bundle.segments[0].wire_id == w1.id
    assert bundle.segments[1].wire_id == w2.id

def test_wire_segment_membership():
    w = Wire(from_conn="A", to_conn="B")
    seg = BundleSegmentMembership(wire_id=w.id, start_node=0, end_node=1)
    w.segment_memberships.append(seg)
    assert w.segment_memberships[0].wire_id == w.id

def test_bundle_and_meta_fields():
    bundle = Bundle(meta={"audit": "required"})
    assert bundle.meta["audit"] == "required"
    w = Wire(from_conn="A", to_conn="B", meta={"audit": "fail"})
    assert w.meta["audit"] == "fail"
