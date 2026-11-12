"""
Tests for Phase 1 emergent bundle inference.

Covers:
- Hybrid detection: near-parallel runs one grid cell apart coalesce, while
  angled/distant runs do not.
- APIManager.recompute_auto_bundles: adds emergent bundles for new shared runs,
  removes them when the run disappears, preserves manual bundles, is idempotent,
  and stays out of the undo stack.
- BundleInferenceService wiring: adding/removing a wire recomputes bundles.
"""
import uuid

import pytest

from core.wire import Wire
from core.bundle import Bundle
from core.harness import Harness
from core.logic import find_wire_overlaps
from api.manager import APIManager
from infra.bundle_inference import BundleInferenceService


def _wire(path_nodes, from_conn="A", to_conn="B"):
    return Wire(
        id=str(uuid.uuid4()),
        from_conn=from_conn,
        to_conn=to_conn,
        path_nodes=path_nodes,
    )


# -- Hybrid detection (grid + proximity) ------------------------------
def test_parallel_runs_one_cell_apart_coalesce():
    # Two horizontal runs 2mm (one grid cell) apart, overlapping in x.
    w1 = _wire([[0, 0], [40, 0]])
    w2 = _wire([[0, 2], [40, 2]])
    groups = find_wire_overlaps([w1, w2], grid_size=2.0)
    assert len(groups) == 1
    assert set(groups[0].wire_ids) == {w1.id, w2.id}


def test_parallel_runs_far_apart_do_not_coalesce():
    w1 = _wire([[0, 0], [40, 0]])
    w2 = _wire([[0, 20], [40, 20]])  # far outside tolerance
    assert find_wire_overlaps([w1, w2], grid_size=2.0) == []


def test_non_overlapping_parallel_runs_do_not_coalesce():
    # Parallel and close, but their projections don't overlap (end to end).
    w1 = _wire([[0, 0], [10, 0]])
    w2 = _wire([[20, 0], [30, 0]])
    assert find_wire_overlaps([w1, w2], grid_size=2.0) == []


def test_angled_runs_do_not_coalesce():
    w1 = _wire([[0, 0], [40, 0]])
    w2 = _wire([[0, 0], [40, 40]])  # 45deg -- not parallel
    assert find_wire_overlaps([w1, w2], grid_size=2.0) == []


# -- Emergent recompute -----------------------------------------------
@pytest.fixture
def api():
    APIManager.reset()
    api = APIManager.get_instance()
    api.context.harness = Harness()
    if hasattr(api.context, 'undo_stack'):
        api.context.undo_stack.clear()
    return api


def test_recompute_adds_emergent_bundle(api):
    w1 = _wire([[0, 0], [40, 0]])
    w2 = _wire([[0, 2], [40, 2]])
    api.context.harness.wires.extend([w1, w2])

    added, removed = api.recompute_auto_bundles()
    assert len(added) == 1 and removed == []
    assert len(api.context.harness.bundles) == 1
    assert api.context.harness.bundles[0].meta.get("auto") is True


def test_recompute_is_idempotent(api):
    w1 = _wire([[0, 0], [40, 0]])
    w2 = _wire([[0, 2], [40, 2]])
    api.context.harness.wires.extend([w1, w2])

    api.recompute_auto_bundles()
    added, removed = api.recompute_auto_bundles()
    assert added == [] and removed == []
    assert len(api.context.harness.bundles) == 1


def test_recompute_removes_stale_bundle_when_wire_removed(api):
    w1 = _wire([[0, 0], [40, 0]])
    w2 = _wire([[0, 2], [40, 2]])
    api.context.harness.wires.extend([w1, w2])
    api.recompute_auto_bundles()
    assert len(api.context.harness.bundles) == 1

    api.context.harness.wires.remove(w2)
    added, removed = api.recompute_auto_bundles()
    assert added == [] and len(removed) == 1
    assert api.context.harness.bundles == []


def test_recompute_preserves_manual_bundle(api):
    manual = Bundle(wire_ids=[], segments=[], meta={"auto": False})
    api.context.harness.bundles.append(manual)
    w1 = _wire([[0, 0], [40, 0]])
    w2 = _wire([[0, 2], [40, 2]])
    api.context.harness.wires.extend([w1, w2])

    api.recompute_auto_bundles()
    assert manual in api.context.harness.bundles
    autos = [b for b in api.context.harness.bundles if b.meta.get("auto")]
    assert len(autos) == 1


def test_recompute_does_not_touch_undo_stack(api):
    w1 = _wire([[0, 0], [40, 0]])
    w2 = _wire([[0, 2], [40, 2]])
    api.context.harness.wires.extend([w1, w2])
    api.recompute_auto_bundles()
    # No command should have been pushed for emergent bundles.
    if hasattr(api.context, 'undo_stack'):
        assert not api.context.undo_stack.can_undo()


def test_recompute_emits_bundle_events(api):
    events = []
    api.subscribe("bundle_added", lambda b: events.append(("added", b)))
    api.subscribe("bundle_removed", lambda b: events.append(("removed", b)))
    w1 = _wire([[0, 0], [40, 0]])
    w2 = _wire([[0, 2], [40, 2]])
    api.context.harness.wires.extend([w1, w2])
    api.recompute_auto_bundles()
    assert any(kind == "added" for kind, _ in events)


# -- Service wiring ---------------------------------------------------
def test_service_recomputes_on_wire_events(api):
    # The observer holds subscribers weakly, so the service must be kept alive
    # (production stores it on ``api.bundle_inference``).
    service = BundleInferenceService(api)
    api.bundle_inference = service
    w1 = _wire([[0, 0], [40, 0]])
    w2 = _wire([[0, 2], [40, 2]])
    api.context.harness.wires.extend([w1, w2])

    # Simulate the wire-added lifecycle event.
    api.dispatch("wire_added", w2)
    autos = [b for b in api.context.harness.bundles if b.meta.get("auto")]
    assert len(autos) == 1

    # Removing a wire and firing the event tears the bundle down.
    api.context.harness.wires.remove(w2)
    api.dispatch("wire_removed", w2)
    autos = [b for b in api.context.harness.bundles if b.meta.get("auto")]
    assert autos == []
