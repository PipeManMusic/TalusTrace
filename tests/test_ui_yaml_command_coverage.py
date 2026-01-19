import pytest
import yaml
from ui.main_window import MainWindow
from api.manager import APIManager
from infra.context import Context
from api.actions import registry
from PySide6.QtWidgets import QApplication
from unittest.mock import patch

@pytest.fixture(scope="function")
def app():
    app = QApplication.instance() or QApplication([])
    yield app

@pytest.fixture(scope="function")
def api_manager():
    APIManager.reset()
    api = APIManager(context=Context())
    yield api

@pytest.fixture(scope="function")
def main_window(app, api_manager):
    window = MainWindow()
    window.api = api_manager
    api_manager.main_window = window
    window.show()
    yield window
    window.close()

def get_all_commands_from_yaml():
    with open("resources/config/ui_layout.yaml", "r") as f:
        config = yaml.safe_load(f)
    commands = set()
    # Menubar
    for menu in config.get("menubar", []):
        for item in menu.get("items", []):
            if isinstance(item, dict) and "command" in item:
                commands.add(item["command"])
    # Toolbar
    for item in config.get("toolbar", {}).get("items", []):
        if isinstance(item, dict) and "command" in item:
            commands.add(item["command"])
        elif isinstance(item, str):
            commands.add(item)
    # Context menu
    for cmenu in config.get("context_menu", {}).values():
        for item in cmenu:
            if isinstance(item, dict) and "command" in item:
                commands.add(item["command"])
            elif isinstance(item, str):
                commands.add(item)
    return commands

def test_all_yaml_commands_registered():
    commands = get_all_commands_from_yaml()
    missing = [cmd for cmd in commands if cmd not in registry]
    assert not missing, f"Missing command registrations: {missing}"

@pytest.mark.usefixtures("main_window")
def test_all_yaml_commands_functional(qtbot, main_window):
    commands = get_all_commands_from_yaml()
    dialog_patches = [
        patch("PySide6.QtWidgets.QFileDialog.getOpenFileName", return_value=("/tmp/fake.yaml", "")),
        patch("PySide6.QtWidgets.QFileDialog.getSaveFileName", return_value=("/tmp/fake.yaml", "")),
        patch("PySide6.QtWidgets.QMessageBox.question", return_value=1),
        patch("PySide6.QtWidgets.QMessageBox.exec_", return_value=1),
        patch("ui.dialogs.settings_dialog.SettingsDialog.exec_", return_value=0),
        patch("ui.dialogs.theme_dialog.ThemeDialog.exec_", return_value=0),
        patch("ui.dialogs.device_wizard.DeviceWizard.exec", return_value=0),
        patch("ui.dialogs.settings_dialog.SettingsDialog.__init__", return_value=None),
        patch("ui.dialogs.theme_dialog.ThemeDialog.__init__", return_value=None),
        patch("ui.dialogs.device_wizard.DeviceWizard.__init__", return_value=None),
    ]
    with dialog_patches[0], dialog_patches[1], dialog_patches[2], dialog_patches[3], dialog_patches[4], dialog_patches[5], dialog_patches[6], dialog_patches[7], dialog_patches[8], dialog_patches[9]:
        for cmd in commands:
            try:
                with qtbot.waitSignal(registry.action_triggered, timeout=1000, raising=False):
                    registry.execute(cmd, main_window.api.context)
            except Exception as e:
                pytest.fail(f"Command '{cmd}' failed: {e}")
