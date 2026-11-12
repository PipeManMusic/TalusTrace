"""
Tests for Phase 3: routable bundle geometry + breakout points.

Covers:
- Bundle.compute_geometry deriving a trunk polyline and breakouts from members.
- Serialization round-trip of trunk path + breakouts.
- recompute_auto_bundles populating geometry on new bundles and refreshing it
  (dispatching bundle_updated) when a member wire moves within the same run.
"""
import uuid

import pytest

from core.wire import Wire
from core.bundle import Bundle, BundleSegmentMembership, BundleBreakout
from core.harness import Harness
from api.manager import APIManager


def _wire(path_nodes, from_conn="A", to_conn="B"):
    return Wire(
        id=str(uuid.uuid4()),
        from_conn=from_conn,
        to_conn=to_conn,
        path_nodes=path_nodes,
    )


# -- Bundle.compute_geometry ------------------------------------------
def test_compute_geometry_derives_trunk_from_shared_run():
    # Wire A runs through a shared middle segment (nodes 1->2).
    a = _wire([[-10, 0], [0, 0], [40, 0], [50, 10]])
    seg = BundleSegmentMembership(wire_id=a.id, start_node=1, end_node=2)
    b = Bundle(wire_ids=[a.id], segments=[seg])

    changed = b.compute_geometry({a.id: a})

    assert changed is True
    assert b.path_nodes == [[0.0, 0.0], [40.0, 0.0]]


def test_compute_geometry_records_breakouts_at_both_ends():
    a = _wire([[-10, 0], [0, 0], [40, 0], [50, 10]])
    seg = BundleSegmentMembership(wire_id=a.id, start_node=1, end_node=2)
    b = Bundle(wire_ids=[a.id], segments=[seg])

    b.compute_geometry({a.id: a})

    # One breakout at the trunk start (toward node 0) and one at the end.
    starts = [bo for bo in b.breakouts if bo.node_index == 0]
    ends = [bo for bo in b.breakouts if bo.node_index == len(b.path_nodes) - 1]
    assert len(starts) == 1 and starts[0].point == [-10.0, 0.0]
    assert len(ends) == 1 and ends[0].point == [50.0, 10.0]


def test_compute_geometry_no_breakout_when_wire_terminates_at_trunk():
    # Wire is exactly the shared run: no continuation, so no breakouts.
    a = _wire([[0, 0], [40, 0]])
    seg = BundleSegmentMembership(wire_id=a.id, start_node=0, end_node=1)
    b = Bundle(wire_ids=[a.id], segments=[seg])

    b.compute_geometry({a.id: a})

    assert b.path_nodes == [[0.0, 0.0], [40.0, 0.0]]
    assert b.breakouts == []


def test_compute_geometry_returns_false_when_unchanged():
    a = _wire([[0, 0], [40, 0]])
    seg = BundleSegmentMembership(wire_id=a.id, start_node=0, end_node=1)
    b = Bundle(wire_ids=[a.id], segments=[seg])

    assert b.compute_geometry({a.id: a}) is True
    assert b.compute_geometry({a.id: a}) is False


# -- Serialization ----------------------------------------------------
def test_bundle_geometry_roundtrips_through_dict():
    a = _wire([[-10, 0], [0, 0], [40, 0], [50, 10]])
    seg = BundleSegmentMembership(wire_id=a.id, start_node=1, end_node=2)
    b = Bundle(wire_ids=[a.id], segments=[seg])
    b.compute_geometry({a.id: a})

    restored = Bundle.from_dict(b.to_dict())

    assert restored.path_nodes == b.path_nodes
    assert len(restored.breakouts) == len(b.breakouts)
    assert all(isinstance(bo, BundleBreakout) for bo in restored.breakouts)
    assert {(bo.node_index, tuple(bo.point)) for bo in restored.breakouts} == \
        {(bo.node_index, tuple(bo.point)) for bo in b.breakouts}


# -- recompute integration --------------------------------------------
@pytest.fixture
def api():
    APIManager.reset()
    a = APIManager.get_instance()
    a.context.harness = Harness()
    if hasattr(a.context, 'undo_stack'):
        a.context.undo_stack.clear()
    return a


def test_recompute_populates_geometry_on_new_bundle(api):
    w1 = _wire([[0, 0], [40, 0]])
    w2 = _wire([[0, 2], [40, 2]])
    api.context.harness.wires.extend([w1, w2])

    added, _ = api.recompute_auto_bundles()

    assert len(added) == 1
    assert len(added[0].path_nodes) == 2


def test_recompute_refreshes_geometry_and_emits_bundle_updated(api):
    w1 = _wire([[0, 0], [40, 0]])
    w2 = _wire([[0, 2], [40, 2]])
    api.context.harness.wires.extend([w1, w2])
    api.recompute_auto_bundles()
    bundle = api.context.harness.bundles[0]
    original_path = list(bundle.path_nodes)

    events = []
    holder = _Sub(events)
    api.subscribe("bundle_updated", holder.on_updated)

    # Move both wires within the same grid key (shift the whole run in y by <1 cell).
    w1.path_nodes = [[0, 0.4], [40, 0.4]]
    w2.path_nodes = [[0, 2.4], [40, 2.4]]
    api.recompute_auto_bundles()

    assert bundle.path_nodes != original_path
    assert any(e is bundle for e in events)


class _Sub:
    """Strongly held subscriber (observer stores callbacks as weakrefs)."""

    def __init__(self, sink):
        self._sink = sink

    def on_updated(self, data):
        self._sink.append(data)
