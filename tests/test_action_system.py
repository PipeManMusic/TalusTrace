import pytest
import yaml
from PySide6.QtCore import Qt, QEvent
from PySide6.QtGui import QKeyEvent, QKeySequence
from PySide6.QtWidgets import QApplication

from api.actions import registry, register_action
from ui.input_system import InputSystem

@pytest.fixture(scope="session")
def qapp():
    return QApplication.instance() or QApplication([])

@pytest.fixture
def temp_action_config(tmp_path):
    config_data = {
        "commands": [
            {"id": "test.move", "label": "Move Test", "default_key": "G"}
        ]
    }
    config_file = tmp_path / "actions_test.yaml"
    with open(config_file, 'w') as f:
        yaml.dump(config_data, f)
    return str(config_file)

def test_end_to_end_key_trigger(qapp, temp_action_config):
    """
    Validates the full flow: Key Press -> Input System -> Registry -> Function.
    """
    input_sys = InputSystem(config_path=temp_action_config)
    result = {"triggered": False}

    @register_action("test.move")
    def move_callback(context):
        result["triggered"] = True

    # Simulate Pressing 'G'
    event = QKeyEvent(QEvent.KeyPress, Qt.Key_G, Qt.NoModifier)
    
    # FIX: Call eventFilter directly instead of handle_event
    consumed = input_sys.eventFilter(None, event)

    assert consumed is True, "Event should be consumed by the filter"
    assert result["triggered"] is True, "Action should be executed"

def test_unknown_key_pass_through(qapp, temp_action_config):
    input_sys = InputSystem(config_path=temp_action_config)
    event = QKeyEvent(QEvent.KeyPress, Qt.Key_X, Qt.NoModifier)
    
    # FIX: Call eventFilter directly
    consumed = input_sys.eventFilter(None, event)
    
    assert consumed is False, "InputSystem should ignore unmapped keys."