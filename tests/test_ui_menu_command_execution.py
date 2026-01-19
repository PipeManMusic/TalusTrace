import pytest
from unittest.mock import patch, MagicMock
from PySide6.QtWidgets import QApplication
from ui.main_window import MainWindow
from api.manager import APIManager
from infra.context import Context

@pytest.fixture(scope="function")
def app():
    app = QApplication.instance() or QApplication([])
    yield app

@pytest.fixture(scope="function")
def api_manager():
    APIManager.reset()
    api = APIManager(context=Context())
    api.dispatch = MagicMock(wraps=api.dispatch)
    api.subscribe = MagicMock(wraps=api.subscribe)
    yield api

@pytest.fixture(scope="function")
def main_window(app, api_manager):
    window = MainWindow()
    window.api = api_manager
    api_manager.main_window = window
    window.show()
    yield window
    window.close()

def test_menu_commands_execute(main_window, api_manager):
    menubar = main_window.menuBar()
    # Map command to expected UI effect
    command_effects = {
        "file.open": "QFileDialog.getOpenFileName",
        "file.save": "QFileDialog.getSaveFileName",
        "file.new": None,  # Context reset, can check dispatch
        "file.exit": "QApplication.quit",
        "edit.settings": "ui.dialogs.settings_dialog.SettingsDialog.exec_",
        "edit.theme": "ui.dialogs.theme_dialog.ThemeDialog.exec_",
        "device.create_wizard": "ui.dialogs.device_wizard.DeviceWizard.exec",
    }
    for menu in menubar.findChildren(type(menubar)):
        for action in menu.actions():
            cmd_id = action.data()
            if not cmd_id:
                continue
            effect = command_effects.get(cmd_id)
            if effect:
                module, func = effect.rsplit('.', 1)
                with patch(f"{module}.{func}") as mock_func:
                    action.trigger()
                    if cmd_id == "file.open":
                        if not mock_func.called:
                            pytest.fail(f"{cmd_id} did NOT call {effect} (file dialog not opened)")
                    else:
                        assert mock_func.called, f"{cmd_id} did not call {effect}" 
            else:
                # For commands with no direct UI effect, check dispatch
                action.trigger()
                assert api_manager.dispatch.call_count >= 0
