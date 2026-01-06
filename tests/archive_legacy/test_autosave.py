import yaml
import pytest
from PySide6.QtWidgets import QApplication

from talustrace.frontend.app import MainWindow


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    return app or QApplication([])


def test_autosave_writes_without_clearing_dirty(qapp, tmp_path):
    win = MainWindow(autosave_dir=tmp_path, restore_policy="skip")
    win.add_device(0, 0, "D", pins=0)
    assert win.dirty is True
    win.autosave_snapshot()
    autosave_file = tmp_path / "autosave.yaml"
    assert autosave_file.exists()
    # dirty flag should remain true after autosave
    assert win.dirty is True


def test_restore_autosave_auto(qapp, tmp_path):
    # prepare autosave file before window instantiation
    autosave_file = tmp_path / "autosave.yaml"
    data = {
        "devices": [
            {"id": "D1", "label": "Restored", "pins": 0, "x": 0, "y": 0}
        ],
        "wires": [],
    }
    with autosave_file.open("w") as f:
        yaml.dump(data, f)

    win = MainWindow(autosave_dir=tmp_path, restore_policy="auto")
    assert len(win.device_items) == 1
    assert win.device_items[0].model.label == "Restored"
    # ensure we did not bind to autosave path for future saves
    assert win.current_path is None
