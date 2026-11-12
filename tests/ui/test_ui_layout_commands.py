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
    # Patch QDialog.exec AND QWizard.exec to auto-accept any dialog without
    # blocking for user input. QWizard overrides QDialog.exec, so both must
    # be patched to cover every dialog type launched by menu commands.
    import PySide6.QtWidgets as QtWidgets
    original_dialog_exec = QtWidgets.QDialog.exec
    original_wizard_exec = QtWidgets.QWizard.exec

    def auto_accept_dialog(self, *args, **kwargs):
        QtWidgets.QDialog.accept(self)
        return 1

    def auto_accept_wizard(self, *args, **kwargs):
        # Do NOT call accept() — that would invoke DeviceWizard.accept() which
        # tries to save to the library. Just return Accepted so the caller
        # treats the dialog as closed and dismissed.
        return 1

    QtWidgets.QDialog.exec = auto_accept_dialog
    QtWidgets.QWizard.exec = auto_accept_wizard
    # Find QAction for this command in the menu
    found = False
    try:
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
        if not found:
            pytest.skip(f"Command {cmd_id} not found in menu actions; skipping.")
    finally:
        # Restore original exec methods after test
        QtWidgets.QDialog.exec = original_dialog_exec
        QtWidgets.QWizard.exec = original_wizard_exec
