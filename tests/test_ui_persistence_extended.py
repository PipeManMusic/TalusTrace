import pytest


@pytest.mark.xfail(reason="Geometry mismatch")
def test_dock_persistence(qtbot):
    """PH6-UI.3: MainWindow must restore panel sizes via QSettings."""
    from ui.main_window import MainWindow
    from PySide6.QtCore import QSettings

    settings = QSettings("TalusTrace", "Test")
    window = MainWindow()
    # Mock a resize of the property dock
    window.prop_dock.resize(500, 800)
    window.save_state(settings)

    new_window = MainWindow()
    new_window.restore_state(settings)
    assert new_window.prop_dock.width() == 500