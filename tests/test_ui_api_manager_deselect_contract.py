import pytest
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow
from api.manager import APIManager

def test_api_manager_deselect_all_exists(qtbot):
    """
    Integration contract: After MainWindow startup, APIManager must have a deselect_all() method for SelectTool compatibility.
    """
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    api = APIManager.get_instance()
    assert hasattr(api, 'deselect_all') and callable(api.deselect_all), "APIManager.deselect_all is missing or not callable."
    window.close()
