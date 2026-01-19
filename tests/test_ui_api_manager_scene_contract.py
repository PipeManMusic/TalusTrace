import pytest
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow
from api.manager import APIManager

def test_api_manager_scene_and_view_set(qtbot):
    """
    Integration contract: After MainWindow startup, APIManager.scene and APIManager.view must be set.
    This ensures tools relying on these attributes do not raise AttributeError during UI operation.
    """
    app = QApplication.instance() or QApplication([])
    window = MainWindow()
    qtbot.addWidget(window)
    window.show()
    api = APIManager.get_instance()
    assert hasattr(api, 'scene') and api.scene is not None, "APIManager.scene was not set by MainWindow startup."
    assert hasattr(api, 'view') and api.view is not None, "APIManager.view was not set by MainWindow startup."
    window.close()
