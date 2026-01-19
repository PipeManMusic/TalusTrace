import pytest
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow
from api.manager import APIManager

def test_api_manager_open_context_menu_exists(qtbot):
    """
    Contract: After MainWindow startup, APIManager must have an open_context_menu() method for SelectTool compatibility.
    """
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    api = APIManager.get_instance()
    assert hasattr(api, 'open_context_menu') and callable(api.open_context_menu), "APIManager.open_context_menu is missing or not callable."
    window.close()
