import pytest
from unittest.mock import MagicMock
from ui.main_window import MainWindow
from api.manager import APIManager

@pytest.fixture
def main_window(qtbot):
    win = MainWindow()
    qtbot.addWidget(win)
    return win

@pytest.fixture
def api_manager():
    APIManager.reset()
    return APIManager()

# Contract: Panel toggle action updates panel state and enforces contract
def test_panel_toggle_contract(main_window, api_manager, monkeypatch, qtbot):
    monkeypatch.setattr(APIManager, 'get_instance', lambda: api_manager)
    api_manager.dispatch_action = MagicMock()

    # Trigger the registered action for project browser panel
    main_window.register_panel_toggles()
    main_window.show()
    dock = main_window.project_browser_dock
    dock.show()
    initial_visibility = dock.isVisible()
    print(f"Initial dock visibility: {initial_visibility}")
    from api.actions import dispatch_action
    dispatch_action('view.toggle_project_browser')
    from PySide6.QtWidgets import QApplication
    QApplication.processEvents()
    print(f"Dock visibility after dispatch: {dock.isVisible()}")
    def visibility_changed():
        return dock.isVisible() != initial_visibility
    qtbot.waitUntil(visibility_changed, timeout=2000)
    assert dock.isVisible() != initial_visibility
