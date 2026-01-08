import pytest
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow
from api.actions import registry, register_action

@pytest.fixture(scope="session")
def qapp():
    return QApplication.instance() or QApplication([])

def test_status_bar_action_feedback(qapp):
    window = MainWindow()
    test_id = "feedback.test_action"
    
    @register_action(test_id)
    def dummy_func(ctx): pass
    
    registry.execute(test_id)
    QApplication.processEvents()
    
    assert test_id in window.statusBar().currentMessage()