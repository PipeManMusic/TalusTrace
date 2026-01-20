import pytest
from ui.main_window import MainWindow
from api.actions import registry
import yaml
import os
from PySide6.QtCore import Qt

def get_yaml_commands():
    # Use workspace root for config path
    config_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../resources/config/ui_layout.yaml"))
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    commands = set()
    for menu in config.get("menubar", []):
        for item in menu.get("items", []):
            if isinstance(item, dict) and "command" in item:
                commands.add(item["command"])
    return commands

@pytest.mark.parametrize("cmd_id", list(get_yaml_commands()))
def test_ui_layout_command_hooked_up(qtbot, cmd_id):
    window = MainWindow()
    qtbot.addWidget(window)
    # Find QAction for this command in the menu
    found = False
    for top_action in window.menuBar().actions():
        menu = top_action.menu()
        if menu:
            for action in menu.actions():
                if action.data() == cmd_id:
                    found = True
                    # Connect to signal and trigger
                    triggered = []
                    def on_triggered(action_id, ctx):
                        triggered.append(action_id)
                    registry.action_triggered.connect(on_triggered)
                    action.trigger()
                    qtbot.wait(10)
                    registry.action_triggered.disconnect(on_triggered)
                    assert cmd_id in triggered, f"Command {cmd_id} not hooked up to registry"
    assert found, f"Command {cmd_id} not found in menu actions"
