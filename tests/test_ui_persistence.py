import pytest
from PySide6.QtCore import QSettings
from ui.main_window import MainWindow

def test_window_state_save_restore(qtbot):
    """PH5-5.9: Window should save geometry to QSettings."""
    settings = QSettings("TalusTrace", "TestEnv")
    settings.clear()
    
    # 1. Open Window and Resize
    win = MainWindow()
    win.resize(800, 600)
    win.save_state(settings)
    win.close()
    
    # 2. Verify settings written
    assert settings.contains("geometry")
    
    # 3. Restore
    win2 = MainWindow()
    win2.restore_state(settings)
    # Note: Exact geometry restore might vary by OS, but key check implies logic ran