import yaml
import pytest
from PySide6.QtWidgets import QApplication
from talustrace.frontend.app import MainWindow


@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


def test_dirty_flag_and_save_roundtrip(qapp, tmp_path):
    win = MainWindow(autosave_dir=tmp_path, restore_policy="skip")
    assert win.dirty is False

    win.add_device(10, 10, "TestDev")
    assert win.dirty is True

    path = tmp_path / "h1.yaml"
    win.save_harness(path)

    assert path.exists()
    assert win.dirty is False
    assert win.current_path == path

    with open(path, "r") as f:
        data = yaml.safe_load(f)

    assert len(data.get("devices", [])) >= 1


def test_recent_files_mru(qapp, tmp_path):
    win = MainWindow(autosave_dir=tmp_path, restore_policy="skip")
    p1 = tmp_path / "a.yaml"
    p2 = tmp_path / "b.yaml"

    win.save_harness(p1)
    win.save_harness(p2)

    assert win.recent_files[0] == p2
    assert p1 in win.recent_files
    assert win.recent_files.count(p2) == 1


def test_load_harness_restores_devices(qapp, tmp_path):
    win = MainWindow(autosave_dir=tmp_path, restore_policy="skip")
    p1 = tmp_path / "base.yaml"
    p2 = tmp_path / "expanded.yaml"

    # Save initial (1 device)
    win.add_device(0, 0, "Base")
    win.save_harness(p1)

    # Add one more device and save
    win.add_device(40, 40, "Extra")
    assert len(win.device_items) >= 2
    win.save_harness(p2)

    # Load the original; device count should match original snapshot
    win.load_harness(p1)
    assert len(win.device_items) == 1
    assert win.dirty is False


def test_new_file_resets_state(qapp, tmp_path):
    win = MainWindow(autosave_dir=tmp_path, restore_policy="skip")
    win.add_device(20, 20, "Temp")
    assert win.dirty is True
    win.new_file()
    assert win.dirty is False
    assert win.current_path is None
    assert len(win.device_items) == 0


def test_save_dialog_appends_yaml_suffix(qapp, tmp_path):
    win = MainWindow(autosave_dir=tmp_path, restore_policy="skip")

    p_no_ext = tmp_path / "sample"
    ensured = win._ensure_yaml_suffix(p_no_ext)
    assert ensured.suffix == ".yaml"

    p_yml = tmp_path / "sample.yml"
    ensured_yml = win._ensure_yaml_suffix(p_yml)
    assert ensured_yml.suffix == ".yml"
