"""
Tests for wire-overlap detection and 'upgrade common section to a bundle'.

Covers:
- core.logic.find_wire_overlaps / build_bundle_from_overlap (pure geometry).
- APIManager.detect_wire_overlaps / create_bundle_from_overlap (undoable, and
  excludes sections already bundled).
"""
import uuid

import pytest

from core.wire import Wire
from core.harness import Harness
from core.logic import find_wire_overlaps, build_bundle_from_overlap, OverlapGroup
from api.manager import APIManager


def _wire(path_nodes, from_conn="A", to_conn="B"):
    return Wire(
        id=str(uuid.uuid4()),
        from_conn=from_conn,
        to_conn=to_conn,
        path_nodes=path_nodes,
    )


# ── Core detection ───────────────────────────────────────────────────
def test_find_overlaps_detects_shared_segment():
    # w1 and w2 both traverse (10,0)->(20,0).
    w1 = _wire([[0, 0], [10, 0], [20, 0]])
    w2 = _wire([[10, 0], [20, 0], [30, 0]])
    groups = find_wire_overlaps([w1, w2], grid_size=2.0)
    assert len(groups) == 1
    g = groups[0]
    assert set(g.wire_ids) == {w1.id, w2.id}
    members = {wid: (s, e) for (wid, s, e) in g.members}
    # w1's shared segment is its 2nd segment (index 1); w2's is its 1st (index 0).
    assert members[w1.id] == (1, 2)
    assert members[w2.id] == (0, 1)


def test_find_overlaps_none_when_disjoint():
    w1 = _wire([[0, 0], [10, 0]])
    w2 = _wire([[0, 50], [10, 50]])
    assert find_wire_overlaps([w1, w2], grid_size=2.0) == []


def test_find_overlaps_single_wire_is_empty():
    w1 = _wire([[0, 0], [10, 0], [20, 0]])
    assert find_wire_overlaps([w1], grid_size=2.0) == []


def test_find_overlaps_three_wires_same_section():
    w1 = _wire([[0, 0], [10, 0]])
    w2 = _wire([[0, 0], [10, 0]])
    w3 = _wire([[0, 0], [10, 0]])
    groups = find_wire_overlaps([w1, w2, w3], grid_size=2.0)
    assert len(groups) == 1
    assert set(groups[0].wire_ids) == {w1.id, w2.id, w3.id}


def test_find_overlaps_excludes_already_bundled():
    w1 = _wire([[0, 0], [10, 0]])
    w2 = _wire([[0, 0], [10, 0]])
    groups = find_wire_overlaps([w1, w2], grid_size=2.0)
    bundle = build_bundle_from_overlap(groups[0])
    # Same overlap should now be excluded because a bundle already covers it.
    again = find_wire_overlaps([w1, w2], grid_size=2.0, existing_bundles=[bundle])
    assert again == []


# ── Bundle construction ──────────────────────────────────────────────
def test_build_bundle_from_overlap_memberships_valid():
    w1 = _wire([[0, 0], [10, 0], [20, 0]])
    w2 = _wire([[10, 0], [20, 0], [30, 0]])
    group = find_wire_overlaps([w1, w2], grid_size=2.0)[0]
    bundle = build_bundle_from_overlap(group)
    assert set(bundle.wire_ids) == {w1.id, w2.id}
    assert len(bundle.segments) == 2
    # Must pass the model's own integrity checks (end_node > start_node etc.).
    bundle.validate_segments()
    assert bundle.meta.get("auto") is True
    assert bundle.meta.get("segment_key") is not None


# ── API integration ──────────────────────────────────────────────────
@pytest.fixture
def api():
    APIManager.reset()
    api = APIManager.get_instance()
    api.context.harness = Harness()
    if hasattr(api.context, 'undo_stack'):
        api.context.undo_stack.clear()
    return api


def test_api_detect_and_create_bundle(api):
    w1 = _wire([[0, 0], [10, 0], [20, 0]])
    w2 = _wire([[10, 0], [20, 0], [30, 0]])
    api.context.harness.wires.extend([w1, w2])

    groups = api.detect_wire_overlaps(w2)
    assert len(groups) == 1

    bundle = api.create_bundle_from_overlap(groups[0])
    assert bundle in api.context.harness.bundles
    assert set(bundle.wire_ids) == {w1.id, w2.id}

    # Re-detecting finds nothing now that the section is bundled.
    assert api.detect_wire_overlaps(w2) == []


def test_api_create_bundle_is_undoable(api):
    w1 = _wire([[0, 0], [10, 0]])
    w2 = _wire([[0, 0], [10, 0]])
    api.context.harness.wires.extend([w1, w2])
    group = api.detect_wire_overlaps()[0]
    bundle = api.create_bundle_from_overlap(group)
    assert bundle in api.context.harness.bundles

    if hasattr(api.context, 'undo_stack'):
        api.context.undo_stack.undo()
        assert bundle not in api.context.harness.bundles
        api.context.undo_stack.redo()
        assert bundle in api.context.harness.bundles


def test_api_detect_filters_by_wire(api):
    # w1/w2 share a section; w3 is elsewhere and unrelated.
    w1 = _wire([[0, 0], [10, 0]])
    w2 = _wire([[0, 0], [10, 0]])
    w3 = _wire([[0, 90], [10, 90]])
    api.context.harness.wires.extend([w1, w2, w3])
    assert api.detect_wire_overlaps(w3) == []
    assert len(api.detect_wire_overlaps(w1)) == 1
