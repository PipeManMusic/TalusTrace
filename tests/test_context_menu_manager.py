import pytest
import yaml
import os
from PySide6.QtWidgets import QMenu
from ui.context_menu_manager import ContextMenuManager
from ui.layout_manager import LayoutManager

def test_context_menu_population_from_yaml(qtbot):
    """
    Verifies that the ContextMenuManager can correctly parse ui_layout.yaml
    and generate a QMenu with actions.
    
    Target Issue: "Context menus aren't being loaded."
    """
    # 1. Setup: Load the real configuration files
    # We use the actual paths to ensure we aren't testing a mock that works while production fails.
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    layout_path = os.path.join(base_dir, "resources", "config", "ui_layout.yaml")
    actions_path = os.path.join(base_dir, "resources", "config", "actions.yaml")
    
    assert os.path.exists(layout_path), "Critical: ui_layout.yaml not found"
    
    # 2. Emulate the Boot Sequence (Loading Configs)
    with open(layout_path, 'r') as f:
        layout_cfg = yaml.safe_load(f)
        
    # We mock actions_map since we are testing menu population, not action loading
    # But checking if the keys exist in layout is crucial.
    actions_map = {
        "device.add_pin": {"label": "Add Pin"},
        "edit.delete": {"label": "Delete Item"}
    }
    
    # 3. Initialize Manager
    manager = ContextMenuManager(layout_cfg, actions_map)
    
    # 4. Action: Attempt to build the 'device' menu
    # defined in ui_layout.yaml as:
    # context_menu:
    #   device:
    #     - command: "device.add_pin"
    device_menu = manager.build_menu("device")
    
    # 5. Assertions
    assert device_menu is not None, "Manager returned None for 'device' menu"
    assert isinstance(device_menu, QMenu)
    
    # Check Action Count (Based on your provided yaml: Add Pin, Separator, Rotate, Separator, Delete)
    actions = device_menu.actions()
    assert len(actions) >= 3, f"Menu unpopulated! Found {len(actions)} actions, expected at least 3."
    
    # Check Specific Action Content
    # The first action should be 'device.add_pin'
    first_action = actions[0]
    assert first_action.data() == "device.add_pin", "First menu item has wrong command ID"
    assert first_action.text() == "Add Pin", "First menu item has wrong label (failed to read actions_map?)"

def test_context_menu_missing_integration(qtbot):
    """
    Proves that MainWindow does not have the manager installed.
    This test expects to FAIL if the code is broken, or PASS if we just want to assert the missing attribute.
    """
    from ui.main_window import MainWindow
    from api.manager import APIManager
    
    APIManager.reset()
    window = MainWindow()
    qtbot.add_widget(window)
    
    # This assertion catches the root cause:
    assert hasattr(window, 'context_menu_manager'), \
        "VIOLATION: MainWindow has no 'context_menu_manager'. The menu logic is dead code."
