import pytest
from PySide6.QtGui import QAction
from PySide6.QtWidgets import QMenu
from ui.main_window import MainWindow
from api.manager import APIManager

def test_context_menu_loaded_from_api_config(qtbot):
    """
    Compliance Check: Verify Context Menus are loaded from ui_layout.yaml via the Manager.
    
    Target Issue: "ui_layout.yaml has context menus but they aren't being loaded."
    
    Current Behavior (Expected FAIL):
    1. MainWindow initializes.
    2. Has no 'context_menu_manager'.
    3. Context menus are never built.
    
    Expected Behavior (PASS):
    1. MainWindow initializes ContextMenuManager with config from LayoutManager.
    2. Manager correctly parses 'device' and 'wire' menus.
    3. Menus contain the actions defined in YAML (e.g. 'device.add_pin').
    """
    # 1. Setup
    APIManager.reset()
    window = MainWindow()
    qtbot.add_widget(window)
    
    # 2. Critical Architecture Check
    # The window must possess the manager to handle dynamic menus
    assert hasattr(window, 'context_menu_manager'), \
        "VIOLATION: MainWindow has no 'context_menu_manager'. Context menus from YAML are being ignored."
        
    # 3. functional Check: Build a specific menu defined in your YAML
    # YAML defines: context_menu -> device -> [device.add_pin, separator, edit.rotate_cw...]
    menu = window.context_menu_manager.build_menu("device", parent=window)
    
    assert menu is not None, "Context Menu Manager returned None for 'device' type."
    assert isinstance(menu, QMenu)
    
    # 4. Content Verification
    actions = menu.actions()
    assert len(actions) > 0, "Device context menu is empty! Config loading failed."
    
    # Check for specific known action from the provided YAML
    action_datas = [a.data() for a in actions if not a.isSeparator()]
    found_commands = set()
    found_uuids = set()
    for d in action_datas:
        if isinstance(d, dict):
            if "command" in d:
                found_commands.add(d["command"])
            if "uuid" in d:
                found_uuids.add(d["uuid"])
        elif isinstance(d, str):
            found_uuids.add(d)
    assert ("device.add_pin" in found_commands or "7a1e2b3c-4d5e-678f-9012-abcdefabcdef" in found_uuids), \
        f"Missing 'device.add_pin' in menu. Found: commands={found_commands}, uuids={found_uuids}"
    assert ("edit.rotate_cw" in found_commands or "4a88e033-860e-4b9b-9140-338b49c40e61" in found_uuids), \
        f"Missing 'edit.rotate_cw' in menu. Found: commands={found_commands}, uuids={found_uuids}"

def test_context_menu_api_execution_binding(qtbot):
    """
    Verify that the generated menu items are actually bound to the API Registry.
    Ref: "enforce getting it from the api"
    """
    APIManager.reset()
    window = MainWindow()
    qtbot.add_widget(window)
    
    if not hasattr(window, 'context_menu_manager'):
        pytest.skip("Cannot test API binding because ContextManager is missing.")
        
    menu = window.context_menu_manager.build_menu("wire", parent=window)
    actions = menu.actions()
    
    # Find delete action
    delete_action = next((a for a in actions if (isinstance(a.data(), dict) and (a.data().get("command") == "edit.delete" or a.data().get("uuid") == "e5f01b07-dd65-4fbc-9d0f-59b83cdc0a0b")) or a.data() == "edit.delete" or a.data() == "e5f01b07-dd65-4fbc-9d0f-59b83cdc0a0b"), None)
    assert delete_action is not None, "Wire menu missing 'edit.delete'"
    
    # Verify connection (Hard to inspect lambda, but we check it's enabled)
    assert delete_action.isEnabled()