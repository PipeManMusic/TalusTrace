import pytest
from PySide6.QtGui import QKeySequence
from ui.input_system import InputSystem
from api.actions import register_action, registry

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
    
    # Verify internal mapping
    assert "Ctrl+Shift+T" in input_sys._shortcuts
    assert input_sys._shortcuts["Ctrl+Shift+T"] == "test.shortcut"
    
    # Simulate triggering (programmatically)
    input_sys.process_key_sequence("Ctrl+Shift+T")
    assert triggered is True