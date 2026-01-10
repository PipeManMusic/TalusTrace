import pytest
from PySide6.QtGui import QKeySequence
from ui.input_system import InputSystem
from api.actions import register_action

def test_shortcut_registration(qtbot):
    """PH5-SHELL.2: InputSystem should map QKeySequence to Actions."""
    input_sys = InputSystem()
    
    # Create a dummy action
    triggered = False
    @register_action("test.shortcut")
    def on_trigger(ctx):
        nonlocal triggered
        triggered = True
    
    # Register Shortcut
    input_sys.register_shortcut("Ctrl+Shift+T", "test.shortcut")
    
    # FIX: Check the actual attribute name used in implementation (key_map)
    normalized_key = QKeySequence("Ctrl+Shift+T").toString()
    assert normalized_key in input_sys.key_map
    assert input_sys.key_map[normalized_key] == "test.shortcut"
