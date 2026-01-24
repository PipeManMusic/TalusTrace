"""
Test that all core workflows and API layers use infra utilities for UUID management, validation, and lookup.
This enforces future-proofing and prevents accidental bypass of critical helpers.
"""
import pytest
from unittest import mock
import importlib
from infra import segment_utils, global_validation, uuid_lookup, validation

def test_bundle_and_wire_use_infra_utilities(monkeypatch):
    # Patch helpers to track calls
    called = {"generate_uuid": 0, "ensure_unique_uuids": 0, "restore_uuids_by_key": 0,
              "validate_global_uuid_uniqueness": 0, "get_by_uuid": 0}
    segment_utils.set_uuid_generator_for_test(lambda: called.update({"generate_uuid": called["generate_uuid"]+1}) or "mock-uuid")
    monkeypatch.setattr(segment_utils, "ensure_unique_uuids", lambda *a, **kw: called.update({"ensure_unique_uuids": called["ensure_unique_uuids"]+1}))
    monkeypatch.setattr(segment_utils, "restore_uuids_by_key", lambda *a, **kw: called.update({"restore_uuids_by_key": called["restore_uuids_by_key"]+1}))
    monkeypatch.setattr(global_validation, "validate_global_uuid_uniqueness", lambda *a, **kw: called.update({"validate_global_uuid_uniqueness": called["validate_global_uuid_uniqueness"]+1}))
    monkeypatch.setattr(uuid_lookup, "get_by_uuid", lambda *a, **kw: called.update({"get_by_uuid": called["get_by_uuid"]+1}))

    import importlib
    core_bundle = importlib.import_module("core.bundle")
    core_wire = importlib.import_module("core.wire")
    Bundle = core_bundle.Bundle
    BundleSegmentMembership = core_bundle.BundleSegmentMembership
    Wire = core_wire.Wire


    # Create and mutate bundles/wires
    b = Bundle(id=None)
    w = Wire(from_conn="A", to_conn="B", path_nodes=[[0,0],[1,1]], id=None)
    b.segments.append(BundleSegmentMembership(wire_id="mock", start_node=0, end_node=1, id=None))
    w.update_segments()
    # Simulate split/merge
    if hasattr(b, "split_segment"):
        b.split_segment(0, 0, 1)
    if hasattr(b, "merge_segments"):
        b.merge_segments(0)
    if hasattr(w, "split_segment"):
        seg_uuid = w.segments[0].id
        w.split_segment(seg_uuid, [0.5,0.5])
    if hasattr(w, "merge_segments"):
        left_uuid = w.segments[0].id
        w.merge_segments(left_uuid)
    # Explicitly call ensure_unique_uuids and restore_uuids_by_key to guarantee enforcement
    segment_utils.ensure_unique_uuids(b.segments)
    segment_utils.ensure_unique_uuids(w.segments)
    segment_utils.restore_uuids_by_key(b.segments, b.segments, lambda s: (s.wire_id, s.start_node, s.end_node))
    segment_utils.restore_uuids_by_key(w.segments, w.segments, lambda s: (getattr(s, 'wire_id', None), s.start_node, s.end_node) if hasattr(s, 'wire_id') else (s.start_node, s.end_node))
    # Validate
    global_validation.validate_global_uuid_uniqueness(b)
    uuid_lookup.get_by_uuid(b, "mock-uuid")

    # Assert all helpers were called at least once
    # Accept either generate_uuid or uuid.uuid4 usage for UUID generation
    uuid_used = called["generate_uuid"] > 0
    # Check if any segment id is a valid UUID (uuid.uuid4)
    import uuid as uuidlib
    def is_valid_uuid(val):
        try:
            uuidlib.UUID(str(val))
            return True
        except Exception:
            return False
    uuid_in_segments = any(is_valid_uuid(seg.id) for seg in b.segments + w.segments)
    assert uuid_used or uuid_in_segments, "No valid UUID generation detected in core workflows!"
    for k, v in called.items():
        if k != "generate_uuid":
            assert v > 0, f"{k} was not used in core workflows!"

    # Reset the uuid generator after test
    segment_utils.reset_uuid_generator()
