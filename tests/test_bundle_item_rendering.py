"""
Tests for Phase 2 bundle rendering (BundleItem + canvas wiring).

Covers:
- BundleItem derives its trunk polyline from member wire geometry.
- Trunk thickness follows the bundle-diameter formula and grows with member count.
- Visibility flag is honored.
- The canvas creates/removes a BundleItem on bundle_added/bundle_removed.
"""
import uuid

import pytest

from core.wire import Wire
from core.bundle import Bundle, BundleSegmentMembership
from core.harness import Harness
from core.logic import build_bundle_from_overlap, find_wire_overlaps
from api.manager import APIManager
from ui.items.bundle import BundleItem


def _wire(path_nodes, diameter_mm=1.0):
    return Wire(
        id=str(uuid.uuid4()),
        from_conn="A",
        to_conn="B",
        path_nodes=path_nodes,
        diameter_mm=diameter_mm,
    )


def test_bundle_item_trunk_follows_member_geometry(qtbot):
    w1 = _wire([[0, 0], [40, 0]])
    w2 = _wire([[0, 2], [40, 2]])
    group = find_wire_overlaps([w1, w2], grid_size=2.0)[0]
    bundle = build_bundle_from_overlap(group)

    item = BundleItem(bundle, {w1.id: w1, w2.id: w2})
    path = item.path()
    assert path.elementCount() == 2  # a single trunk segment
    # Endpoints match the first resolvable member's shared segment.
    start = path.elementAt(0)
    end = path.elementAt(1)
    assert (start.x, start.y) == (0.0, 0.0)
    assert (end.x, end.y) == (40.0, 0.0)


def test_bundle_item_empty_without_lookup(qtbot):
    w1 = _wire([[0, 0], [40, 0]])
    w2 = _wire([[0, 2], [40, 2]])
    group = find_wire_overlaps([w1, w2], grid_size=2.0)[0]
    bundle = build_bundle_from_overlap(group)

    item = BundleItem(bundle, None)
    assert item.path().elementCount() == 0


def test_bundle_trunk_thickness_grows_with_member_count(qtbot):
    w1 = _wire([[0, 0], [40, 0]])
    w2 = _wire([[0, 2], [40, 2]])
    w3 = _wire([[0, 4], [40, 4]])
    lookup = {w.id: w for w in (w1, w2, w3)}

    g2 = find_wire_overlaps([w1, w2], grid_size=2.0)[0]
    g3 = find_wire_overlaps([w1, w2, w3], grid_size=2.0)[0]
    item2 = BundleItem(build_bundle_from_overlap(g2), lookup)
    item3 = BundleItem(build_bundle_from_overlap(g3), lookup)

    assert item3.pen().widthF() > item2.pen().widthF()


def test_bundle_item_respects_visibility(qtbot):
    w1 = _wire([[0, 0], [40, 0]])
    w2 = _wire([[0, 2], [40, 2]])
    group = find_wire_overlaps([w1, w2], grid_size=2.0)[0]
    bundle = build_bundle_from_overlap(group)
    bundle.visible = False

    item = BundleItem(bundle, {w1.id: w1, w2.id: w2})
    assert item.isVisible() is False


def test_bundle_item_draws_below_wires(qtbot):
    w1 = _wire([[0, 0], [40, 0]])
    w2 = _wire([[0, 2], [40, 2]])
    group = find_wire_overlaps([w1, w2], grid_size=2.0)[0]
    item = BundleItem(build_bundle_from_overlap(group), {w1.id: w1, w2.id: w2})
    # Wires sit at z=15; the trunk must render beneath them.
    assert item.zValue() < 15


def test_bundle_item_draws_breakout_stubs(qtbot):
    # Wires continue past the shared run, so the bundle has breakout points.
    w1 = _wire([[-10, 0], [0, 0], [40, 0], [50, 0]])
    w2 = _wire([[-10, 2], [0, 2], [40, 2], [50, 2]])
    lookup = {w1.id: w1, w2.id: w2}
    group = find_wire_overlaps([w1, w2], grid_size=2.0)[0]
    bundle = build_bundle_from_overlap(group)
    bundle.compute_geometry(lookup)
    assert bundle.breakouts, "expected breakouts for wires extending past the run"

    item = BundleItem(bundle, lookup)
    # Trunk (2 elements) plus one moveTo+lineTo per breakout stub.
    assert item.path().elementCount() == 2 + 2 * len(bundle.breakouts)



# ── Canvas wiring ────────────────────────────────────────────────────
@pytest.fixture
def api():
    APIManager.reset()
    api = APIManager.get_instance()
    api.context.harness = Harness()
    if hasattr(api.context, 'undo_stack'):
        api.context.undo_stack.clear()
    return api


def test_canvas_adds_and_removes_bundle_item(api, qtbot):
    from ui.canvas import HarnessCanvas
    canvas = HarnessCanvas()
    qtbot.addWidget(canvas)

    w1 = _wire([[0, 0], [40, 0]])
    w2 = _wire([[0, 2], [40, 2]])
    api.context.harness.wires.extend([w1, w2])

    added, _ = api.recompute_auto_bundles()
    bundle = added[0]
    # bundle_added was dispatched; canvas should have created a BundleItem.
    assert api.get_scene_item(bundle.id) is not None
    assert isinstance(api.get_scene_item(bundle.id), BundleItem)

    api.context.harness.wires.remove(w2)
    api.recompute_auto_bundles()
    assert api.get_scene_item(bundle.id) is None


def test_canvas_refreshes_bundle_item_on_update(api, qtbot):
    from ui.canvas import HarnessCanvas
    canvas = HarnessCanvas()
    qtbot.addWidget(canvas)

    w1 = _wire([[0, 0], [40, 0]])
    w2 = _wire([[0, 2], [40, 2]])
    api.context.harness.wires.extend([w1, w2])
    added, _ = api.recompute_auto_bundles()
    bundle = added[0]
    item = api.get_scene_item(bundle.id)
    old_start = item.path().elementAt(0)
    old_xy = (old_start.x, old_start.y)

    # Move the run within the same grid key -> bundle_updated refreshes the item.
    w1.path_nodes = [[0, 0.4], [40, 0.4]]
    w2.path_nodes = [[0, 2.4], [40, 2.4]]
    api.recompute_auto_bundles()

    new_start = item.path().elementAt(0)
    assert (new_start.x, new_start.y) != old_xy
