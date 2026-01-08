import pytest
from PySide6.QtWidgets import QApplication
# Target Implementation: ui/main_window.py
from ui.main_window import MainWindow
from ui.canvas import HarnessCanvas
from api.manager import APIManager

@pytest.fixture(scope="session")
def qapp():
    return QApplication.instance() or QApplication([])

def test_main_window_structure(qapp):
    window = MainWindow()
    assert isinstance(window.centralWidget(), HarnessCanvas)
    assert "Talus Trace" in window.windowTitle()

def test_global_input_system_installation(qapp):
    window = MainWindow()
    api = APIManager()
    assert api.input_system is not None