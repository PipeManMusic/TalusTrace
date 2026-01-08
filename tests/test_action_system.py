import pytest
import yaml
from PySide6.QtCore import Qt, QEvent
from PySide6.QtGui import QKeyEvent, QKeySequence

# Import SUT (System Under Test)
from api.actions import registry, register_action
from ui.input_system import InputSystem

# ==========================================
# FIXTURES
# ==========================================

@pytest.fixture
def temp_action_config(tmp_path):
    """
    Creates a temporary actions.yaml for testing 
    to avoid modifying/reading the real production config.
    """
    config_data = {
        "commands": [
            {
                "id": "test.move", 
                "label": "Move Test", 
                "default_key": "G"
            },
            {
                "id": "test.save", 
                "label": "Save Test", 
                "default_key": "Ctrl+S"
            }
        ]
    }
    
    config_file = tmp_path / "actions_test.yaml"
    with open(config_file, 'w') as f:
        yaml.dump(config_data, f)
        
    return str(config_file)

# ==========================================
# TESTS
# ==========================================

def test_registry_registration_and_execution():
    """
    Validates api/actions.py: 
    Can we register a function and call it by string ID?
    """
    # 1. Setup - Mock Action
    execution_log = {"called": False}

    @register_action("unit_test.action_1")
    def my_test_action(context):
        execution_log["called"] = True

    # 2. Execution - Call via Registry
    registry.execute("unit_test.action_1")

    # 3. Assertion
    assert execution_log["called"] is True, "Registry failed to execute the registered function."

def test_input_system_loading(temp_action_config):
    """
    Validates ui/input_system.py: 
    Does it parse the YAML and build the Key Map?
    """
    # 1. Load System with Temp Config
    input_sys = InputSystem(config_path=temp_action_config)

    # 2. Verify Mapping
    # Qt normalizes key strings (e.g. "G" -> "G")
    key_g = QKeySequence("G").toString()
    key_save = QKeySequence("Ctrl+S").toString()

    assert key_g in input_sys.key_map
    assert input_sys.key_map[key_g] == "test.move"

    assert key_save in input_sys.key_map
    assert input_sys.key_map[key_save] == "test.save"

def test_end_to_end_key_trigger(temp_action_config):
    """
    Validates the full flow: Key Press -> Input System -> Registry -> Function.
    """
    # 1. Setup
    input_sys = InputSystem(config_path=temp_action_config)
    result = {"triggered": False}

    # Register the action referenced in the YAML ("test.move")
    @register_action("test.move")
    def move_callback(context):
        result["triggered"] = True

    # 2. Simulate User Input (Pressing 'G')
    # QKeyEvent(Type, Key, Modifiers)
    event = QKeyEvent(QEvent.KeyPress, Qt.Key_G, Qt.NoModifier)

    # 3. Handle Event
    consumed = input_sys.handle_event(event)

    # 4. Assertions
    assert consumed is True, "InputSystem should claim the known key event."
    assert result["triggered"] is True, "The Python callback was not fired by the Key Event."

def test_unknown_key_pass_through(temp_action_config):
    """
    Ensures unknown keys are ignored (so the Canvas can handle them if needed).
    """
    input_sys = InputSystem(config_path=temp_action_config)
    
    # Simulate 'X' (not in config)
    event = QKeyEvent(QEvent.KeyPress, Qt.Key_X, Qt.NoModifier)
    
    consumed = input_sys.handle_event(event)
    
    assert consumed is False, "InputSystem should ignore unmapped keys."