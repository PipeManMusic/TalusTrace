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
    input_sys.register_shortcut("T", "test.shortcut")

    # FIX: Check the actual attribute name used in implementation (key_map)
    normalized_key = QKeySequence("Ctrl+Shift+T").toString()
    # The InputSystem uses Qt.Key enums as keys, not stringified QKeySequence
    # So we check the global_keymap for the correct Qt.Key value
    from PySide6.QtCore import Qt
    print("[DEBUG] global_keymap after registration:", input_sys.global_keymap)
    assert Qt.Key_T in input_sys.global_keymap, f"Qt.Key_T not in global_keymap: {input_sys.global_keymap}"
    assert input_sys.global_keymap[Qt.Key_T] == "test.shortcut"
