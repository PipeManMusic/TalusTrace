"""Integration tests for the Library panel placing saved parts into the harness."""
import os
from unittest.mock import patch

import pytest
import yaml

from PySide6.QtCore import Qt

from api.manager import APIManager
from core.library_manager import LibraryManager


@pytest.fixture
def isolated_library(tmp_path):
    """Redirect LibraryManager IO to a tmp parts.yaml with one known entry."""
    parts_path = tmp_path / "parts.yaml"
    parts_path.write_text(
        yaml.safe_dump(
            {
                "parts": {
                    "TEST-CONN-2P": {
                        "name": "Test Connector 2P",
                        "category": "Connectors",
                        "manufacturer": "ACME",
                        "width_mm": 10.0,
                        "height_mm": 5.0,
                        "pins": [
                            {"id": "1", "label": "1", "signal": "", "x": -2.5, "y": 0.0},
                            {"id": "2", "label": "2", "signal": "", "x": 2.5, "y": 0.0},
                        ],
                    }
                }
            }
        )
    )
    patcher = patch.object(
        LibraryManager,
        "_resolve_path",
        lambda self, filename: str(tmp_path / filename),
    )
    patcher.start()
    # Also patch _load_file so the APIManager-owned LibraryManager reads our tmp file
    orig_load = LibraryManager._load_file

    def _patched_load(self, filename):
        target = str(tmp_path / filename)
        if not os.path.exists(target):
            return {}
        with open(target, "r") as f:
            data = yaml.safe_load(f) or {}
        key = filename.replace(".yaml", "")
        return data.get(key, data)

    load_patcher = patch.object(LibraryManager, "_load_file", _patched_load)
    load_patcher.start()
    yield tmp_path
    patcher.stop()
    load_patcher.stop()


def test_library_panel_refresh_shows_saved_parts(qtbot, isolated_library):
    from ui.panels.library import LibraryPanel

    APIManager.reset()
    api = APIManager.get_instance()
    api.library.reload()

    panel = LibraryPanel()
    qtbot.addWidget(panel)

    # Walk the tree and collect leaf items (child of a category).
    leaves = []
    for i in range(panel.tree.topLevelItemCount()):
        top = panel.tree.topLevelItem(i)
        for j in range(top.childCount()):
            leaves.append(top.child(j))

    assert any(leaf.data(0, Qt.UserRole) == "TEST-CONN-2P" for leaf in leaves)


def test_library_panel_double_click_places_device(qtbot, isolated_library):
    from ui.panels.library import LibraryPanel

    APIManager.reset()
    api = APIManager.get_instance()
    api.library.reload()

    panel = LibraryPanel()
    qtbot.addWidget(panel)

    # Find the leaf for TEST-CONN-2P
    leaf = None
    for i in range(panel.tree.topLevelItemCount()):
        top = panel.tree.topLevelItem(i)
        for j in range(top.childCount()):
            child = top.child(j)
            if child.data(0, Qt.UserRole) == "TEST-CONN-2P":
                leaf = child
                break
        if leaf:
            break
    assert leaf is not None

    initial = len(api.context.harness.devices)
    # Simulate a double-click directly via the handler (platform-independent).
    panel._on_item_double_clicked(leaf, 0)

    assert len(api.context.harness.devices) == initial + 1
    new_dev = api.context.harness.devices[-1]
    # The newly placed device must carry pins from the library definition.
    assert len(new_dev.pins) == 2
    labels = {p.label for p in new_dev.pins}
    assert labels == {"1", "2"}


def test_delete_library_part_removes_from_yaml_and_cache(isolated_library):
    APIManager.reset()
    api = APIManager.get_instance()
    api.library.reload()

    assert "TEST-CONN-2P" in api.library.get_parts()

    removed = api.delete_library_part("TEST-CONN-2P")

    assert removed is True
    assert "TEST-CONN-2P" not in api.library.get_parts()
    # Persisted to disk as well.
    on_disk = yaml.safe_load((isolated_library / "parts.yaml").read_text()) or {}
    assert "TEST-CONN-2P" not in on_disk.get("parts", {})


def test_delete_library_part_missing_returns_false(isolated_library):
    APIManager.reset()
    api = APIManager.get_instance()
    api.library.reload()

    assert api.delete_library_part("DOES-NOT-EXIST") is False


def test_library_panel_delete_removes_leaf(qtbot, isolated_library):
    from ui.panels.library import LibraryPanel
    from PySide6.QtWidgets import QMessageBox

    APIManager.reset()
    api = APIManager.get_instance()
    api.library.reload()

    panel = LibraryPanel()
    qtbot.addWidget(panel)

    def _leaf_ids():
        ids = []
        for i in range(panel.tree.topLevelItemCount()):
            top = panel.tree.topLevelItem(i)
            for j in range(top.childCount()):
                ids.append(top.child(j).data(0, Qt.UserRole))
        return ids

    assert "TEST-CONN-2P" in _leaf_ids()

    # Confirm the deletion prompt automatically.
    with patch.object(QMessageBox, "question", return_value=QMessageBox.Yes):
        panel.delete_part("TEST-CONN-2P", "Test Connector 2P")

    assert "TEST-CONN-2P" not in _leaf_ids()


def test_library_panel_delete_cancel_keeps_part(qtbot, isolated_library):
    from ui.panels.library import LibraryPanel
    from PySide6.QtWidgets import QMessageBox

    APIManager.reset()
    api = APIManager.get_instance()
    api.library.reload()

    panel = LibraryPanel()
    qtbot.addWidget(panel)

    # Decline the deletion prompt: the part must survive.
    with patch.object(QMessageBox, "question", return_value=QMessageBox.No):
        panel.delete_part("TEST-CONN-2P", "Test Connector 2P")

    assert "TEST-CONN-2P" in api.library.get_parts()


def test_library_changed_event_refreshes_panel(qtbot, isolated_library):
    """Saving a new part must update the tree live via the library_changed event."""
    from ui.panels.library import LibraryPanel

    APIManager.reset()
    api = APIManager.get_instance()
    api.library.reload()

    panel = LibraryPanel()
    qtbot.addWidget(panel)

    def _leaf_ids():
        ids = []
        for i in range(panel.tree.topLevelItemCount()):
            top = panel.tree.topLevelItem(i)
            for j in range(top.childCount()):
                ids.append(top.child(j).data(0, Qt.UserRole))
        return ids

    assert "NEW-PART-9X" not in _leaf_ids()

    # Simulate the wizard saving a new part then broadcasting the change.
    api.library.save_part(
        "NEW-PART-9X",
        {"name": "New Part", "category": "Connectors", "pins": []},
    )
    api.dispatch("library_changed", {"part_id": "NEW-PART-9X"})

    # The panel should have refreshed itself in response to the event.
    assert "NEW-PART-9X" in _leaf_ids()


