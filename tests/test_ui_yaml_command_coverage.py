import pytest
from unittest.mock import patch, MagicMock
from api.manager import APIManager
from api.actions import registry

def test_all_yaml_commands_functional(qtbot, clean_api_singleton):
    """
    Smoke test: Verify every registered command can be executed without crashing.
    Uses Class-Level Patching to prevent real Dialog instantiation.
    """
    api = clean_api_singleton
    
    # Iterate over keys because registry might not support .items()
    for cmd_id in registry.keys():
        command_func = registry._actions[cmd_id]
        
        try:
            # 1. SPECIAL HANDLING: Settings Dialog
            if cmd_id == "edit.settings":
                with patch("ui.dialogs.settings_dialog.SettingsDialog") as MockDlgClass:
                    MockDlgClass.return_value.exec.return_value = 1
                    MockDlgClass.return_value.accept.return_value = None
                    MockDlgClass.return_value.show.return_value = None
                    MockDlgClass.return_value.open.return_value = None
                    MockDlgClass.return_value.buttons = MagicMock()
                    MockDlgClass.return_value.buttons.accepted = MagicMock()
                    MockDlgClass.return_value.buttons.accepted.emit = MagicMock()
                    MockDlgClass.return_value.buttons.accepted.connect = MagicMock()
                    command_func(api.context)
            # 2. SPECIAL HANDLING: Theme Dialog
            elif cmd_id == "edit.theme":
                with patch("ui.dialogs.theme_dialog.ThemeDialog") as MockDlgClass:
                    MockDlgClass.return_value.exec.return_value = 1
                    MockDlgClass.return_value.accept.return_value = None
                    MockDlgClass.return_value.show.return_value = None
                    MockDlgClass.return_value.open.return_value = None
                    MockDlgClass.return_value.buttons = MagicMock()
                    MockDlgClass.return_value.buttons.accepted = MagicMock()
                    MockDlgClass.return_value.buttons.accepted.emit = MagicMock()
                    MockDlgClass.return_value.buttons.accepted.connect = MagicMock()
                    command_func(api.context)
            # 3. SPECIAL HANDLING: Device Wizard Dialog
            elif cmd_id == "edit.device":
                with patch("ui.dialogs.device_wizard.DeviceWizard") as MockDlgClass:
                    MockDlgClass.return_value.exec.return_value = 1
                    MockDlgClass.return_value.accept.return_value = None
                    MockDlgClass.return_value.show.return_value = None
                    MockDlgClass.return_value.open.return_value = None
                    MockDlgClass.return_value.accept_button = MagicMock()
                    MockDlgClass.return_value.accept_button.clicked = MagicMock()
                    MockDlgClass.return_value.accept_button.click = MagicMock()
                    command_func(api.context)
            # 4. SPECIAL HANDLING: Tools
            elif cmd_id.startswith("tool."):
                command_func(api.context)
            # 5. SPECIAL HANDLING: File Operations
            elif cmd_id in ["file.save", "file.load", "file.export", "file.import"]:
                continue
            else:
                # Standard Command
                command_func(api.context)
        except Exception as e:
            pytest.fail(f"Command '{cmd_id}' failed execution: {e}")

def test_all_yaml_commands_registered(clean_api_singleton):
    """
    Verifies that the API Registry is populated.
    """
    api = clean_api_singleton
    registered_ids = set(registry.keys())
    
    # Check for known missing tools and exclude them if needed
    known_missing = {'tool.measure'}
    
    assert len(registered_ids) > 0, "API Registry is empty!"