import pytest
from PySide6.QtCore import QSettings, Qt
from ui.main_window import MainWindow

def test_dock_persistence(qtbot):
    """PH6-UI.3: MainWindow must restore panel sizes via QSettings."""
    # 1. Setup Environment
    # Use a unique organization/app name to avoid conflicts with other tests
    settings = QSettings("TalusTrace", "TestDockPersistence")
    settings.clear()

    # 2. Create Initial Window
    window = MainWindow()
    window.show()
    qtbot.waitExposed(window)
    
    # Allow layout to stabilize
    qtbot.wait(100)

    # 3. Modify Dock State via QMainWindow API
    # directly resizing window.prop_dock doesn't work well in layouts.
    # We must use resizeDocks([dock], [size], orientation)
    target_width = 500
    window.resizeDocks([window.prop_dock], [target_width], Qt.Horizontal)
    
    # Wait for resize to take effect
    qtbot.wait(100)
    
    # Capture the *actual* width resulting from constraints
    actual_width_before = window.prop_dock.width()
    
    # 4. Save State
    window.save_state(settings)
    window.close()

    # 5. Restore State in New Window
    new_window = MainWindow()
    new_window.show()
    qtbot.waitExposed(new_window)
    
    new_window.restore_state(settings)
    qtbot.wait(100) # Allow layout to re-apply

    # 6. Verify
    actual_width_after = new_window.prop_dock.width()
    
    # Assert within tolerance (e.g. 10px) to account for frame borders/rounding
    assert abs(actual_width_after - actual_width_before) < 10
    
    new_window.close()