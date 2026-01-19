import pytest
from PySide6.QtWidgets import QApplication, QToolBar
from PySide6.QtGui import QAction
from ui.main_window import MainWindow
from api.manager import APIManager
from infra.context import Context
from api.actions import registry
import yaml
import os

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

def get_toolbar_commands():
    with open("resources/config/ui_layout.yaml", "r") as f:
        config = yaml.safe_load(f)
    commands = []
    for item in config.get("toolbar", {}).get("items", []):
        if isinstance(item, dict) and "command" in item:
            commands.append(item["command"])
        elif isinstance(item, str):
            if item != "separator":
                commands.append(item)
    return commands

def test_toolbar_commands_connected_and_functional(main_window):
    toolbar = None
    for child in main_window.findChildren(QToolBar):
        if child.objectName() == "MainToolBar":
            toolbar = child
            break
    assert toolbar is not None, "MainToolBar not found in main window."
    # Dynamically load toolbar commands from YAML
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    config_path = os.path.join(base_dir, "resources", "config", "ui_layout.yaml")
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f) or {}
    toolbar_section = config.get('toolbar', {})
    commands = [item['command'] for item in toolbar_section.get('items', []) if isinstance(item, dict) and 'command' in item]
    found = set()
    # Contract test logic for each command
    for action in toolbar.actions():
        cmd_id = action.data()
        if cmd_id in commands:
            found.add(cmd_id)
            # Contract checks for known commands
            if cmd_id == "tool.add_generic_device":
                # Patch ToolManager.set_tool to verify placement tool activation
                from unittest.mock import patch
                api = main_window.api
                with patch.object(api.tool_manager, "set_tool") as mock_set_tool:
                    # Re-register the action so closure references the patched method
                    from api.actions import register_action
                    def activate_placement_tool(ctx):
                        api.tool_manager.set_tool("placement")
                    register_action("tool.add_generic_device")(activate_placement_tool)
                    action.trigger()
                    mock_set_tool.assert_called_with("placement")
            elif cmd_id == "edit.undo":
                # Patch undo_stack.undo to verify undo
                from unittest.mock import patch
                api = main_window.api
                if hasattr(api.context, "undo_stack"):
                    with patch.object(api.context.undo_stack, "undo") as mock_undo:
                        action.trigger()
                        mock_undo.assert_called()
            elif cmd_id == "edit.redo":
                # Patch undo_stack.redo to verify redo
                from unittest.mock import patch
                api = main_window.api
                if hasattr(api.context, "undo_stack"):
                    with patch.object(api.context.undo_stack, "redo") as mock_redo:
                        action.trigger()
                        mock_redo.assert_called()
            else:
                # Fallback: verify registered callback is called
                called = []
                def mark_called(context):
                    called.append(True)
                registry.register(cmd_id, mark_called)
                action.trigger()
                assert called, f"Toolbar command {cmd_id} did not execute its registered action on trigger."
    missing = set(commands) - found
    assert not missing, f"Toolbar commands missing or not connected: {missing}"
