"""
Tests for project-browser visibility toggling and visibility groups.

Covers:
- Model round-trip of the ``visible`` flag (device, wire, bundle).
- Undoable per-item visibility via APIManager.set_item_visibility.
- User-defined visibility groups (create/rename/delete/membership) and
  group-level show/hide, all undoable and persisted in harness.meta.
"""
import uuid
import pytest

from api.manager import APIManager
from core.device import Device
from core.wire import Wire
from core.bundle import Bundle


def _new_id():
    return str(uuid.uuid4())


@pytest.fixture
def api():
    APIManager.reset()
    return APIManager.get_instance()


# ── Model serialization ──────────────────────────────────────────────
def test_device_visible_roundtrip():
    dev = Device(id=_new_id(), label="D1", visible=False)
    assert Device.from_dict(dev.to_dict()).visible is False
    dev2 = Device(id=_new_id(), label="D2")
    assert dev2.visible is True
    assert Device.from_dict(dev2.to_dict()).visible is True


def test_wire_visible_roundtrip():
    w = Wire(id=_new_id(), visible=False)
    assert Wire.from_dict(w.to_dict()).visible is False


def test_bundle_visible_roundtrip():
    b = Bundle(id=_new_id(), visible=False)
    assert Bundle.from_dict(b.to_dict()).visible is False


def test_missing_visible_defaults_true():
    # Legacy payloads without the field default to visible.
    assert Device.from_dict({"id": _new_id()}).visible is True
    assert Wire.from_dict({"id": _new_id()}).visible is True
    assert Bundle.from_dict({"id": _new_id()}).visible is True


# ── Per-item visibility (undoable) ───────────────────────────────────
def test_set_item_visibility_and_undo(api):
    dev = api.create_device("Test Device")
    assert dev.visible is True

    api.set_item_visibility(dev.id, False)
    assert dev.visible is False

    api.context.undo_stack.undo()
    assert dev.visible is True

    api.context.undo_stack.redo()
    assert dev.visible is False


def test_set_item_visibility_multiple(api):
    d1 = api.create_device("A")
    d2 = api.create_device("B")
    api.set_item_visibility([d1.id, d2.id], False)
    assert d1.visible is False and d2.visible is False
    api.context.undo_stack.undo()
    assert d1.visible is True and d2.visible is True


def test_find_item_by_id_resolves_all_kinds(api):
    dev = api.create_device("A")
    wire = Wire(id=_new_id())
    bundle = Bundle(id=_new_id())
    api.context.harness.wires.append(wire)
    api.context.harness.bundles.append(bundle)
    assert api.find_item_by_id(dev.id) is dev
    assert api.find_item_by_id(wire.id) is wire
    assert api.find_item_by_id(bundle.id) is bundle
    assert api.find_item_by_id("missing") is None


# ── Visibility groups ────────────────────────────────────────────────
def test_create_group_persisted_and_undoable(api):
    d1 = api.create_device("A")
    gid = api.create_visibility_group("Panel", [d1.id])
    groups = api.get_visibility_groups()
    assert len(groups) == 1
    assert groups[0]["name"] == "Panel"
    assert groups[0]["members"] == [d1.id]
    # Persisted in the serialized harness meta.
    assert api.context.harness.to_dict()["meta"]["visibility_groups"][0]["id"] == gid

    api.context.undo_stack.undo()
    assert api.get_visibility_groups() == []


def test_rename_and_delete_group(api):
    gid = api.create_visibility_group("Old")
    api.rename_visibility_group(gid, "New")
    assert api.get_visibility_groups()[0]["name"] == "New"
    api.delete_visibility_group(gid)
    assert api.get_visibility_groups() == []
    # Undo delete restores the (renamed) group.
    api.context.undo_stack.undo()
    assert api.get_visibility_groups()[0]["name"] == "New"


def test_group_membership_add_remove(api):
    d1 = api.create_device("A")
    d2 = api.create_device("B")
    gid = api.create_visibility_group("G")
    api.add_items_to_group(gid, [d1.id, d2.id])
    api.add_items_to_group(gid, [d1.id])  # de-duplicated
    assert api.get_visibility_groups()[0]["members"] == [d1.id, d2.id]
    api.remove_items_from_group(gid, [d1.id])
    assert api.get_visibility_groups()[0]["members"] == [d2.id]


def test_set_group_visibility_toggles_members(api):
    d1 = api.create_device("A")
    d2 = api.create_device("B")
    gid = api.create_visibility_group("G", [d1.id, d2.id])
    api.set_group_visibility(gid, False)
    assert d1.visible is False and d2.visible is False
    api.context.undo_stack.undo()
    assert d1.visible is True and d2.visible is True


# ── Project browser checkbox (crash regression) ──────────────────────
def test_checkbox_toggle_does_not_rebuild_reentrantly(api):
    """
    Toggling an item's checkbox must not rebuild the tree synchronously from
    inside the ``itemChanged`` signal — that deletes the emitting QTreeWidgetItem
    while its C++ signal is on the stack (use-after-free / segfault). The rebuild
    must be deferred to the next event-loop iteration.
    """
    pytest.importorskip("PySide6")
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import Qt, QCoreApplication
    from ui.panels.project_browser import ProjectBrowser, ROLE_ID, ROLE_KIND

    _app = QApplication.instance() or QApplication([])

    d1 = api.create_device("A")
    d2 = api.create_device("B")
    wire = Wire(id=_new_id(), from_conn=d1.id, to_conn=d2.id, path_nodes=[[0, 0], [1, 0]])
    api.context.harness.wires.append(wire)

    pb = ProjectBrowser()
    pb.refresh()

    def find_leaf(item_id):
        root = pb.tree.invisibleRootItem()
        stack = [root.child(i) for i in range(root.childCount())]
        while stack:
            node = stack.pop()
            if node.data(0, ROLE_ID) == item_id and node.data(0, ROLE_KIND) == "wire":
                return node
            stack.extend(node.child(i) for i in range(node.childCount()))
        return None

    def pump():
        for _ in range(5):
            QCoreApplication.processEvents()

    node = find_leaf(wire.id)
    assert node is not None

    # Toggle OFF: the model updates immediately; the tree rebuild is deferred.
    node.setCheckState(0, Qt.Unchecked)
    assert wire.visible is False
    assert pb._refresh_pending is True  # rebuild scheduled, not run inline
    pump()
    assert pb._refresh_pending is False

    # Toggle ON again (the reported crash) — item was recreated by the deferred
    # rebuild, so fetch a fresh reference.
    node = find_leaf(wire.id)
    assert node is not None
    node.setCheckState(0, Qt.Checked)
    assert wire.visible is True
    pump()
    # Tree reflects the restored visibility.
    node = find_leaf(wire.id)
    assert node.checkState(0) == Qt.Checked

    pb.deleteLater()

