import pytest
from unittest.mock import MagicMock, patch
from ui.panels.library import LibraryPanel
from api.manager import APIManager

def test_library_panel_io_compliance(qtbot):
    """
    Compliance Check: Initialization Phase 5 (The Subscribers).
    
    Current Behavior (Risk): Panel imports 'yaml' and reads files directly.
    Expected Behavior (Compliant): Panel iterates 'api.library.parts'.
    """
    # 1. Setup API with Mock Data
    APIManager.reset()
    api = APIManager.get_instance()
    
    # Populate Core Library with unique test data
    mock_parts = [
        {"id": "TEST_PART_A", "category": "Connectors"},
        {"id": "TEST_PART_B", "category": "Splices"}
    ]
    api.library = MagicMock()
    api.library.parts = mock_parts
    api.library.get_parts.return_value = mock_parts

    # 2. Trap File IO
    # We patch 'open' to fail. If the panel tries to read a file, it crashes the test.
    with patch("builtins.open", side_effect=PermissionError("VIOLATION: UI accessed File System!")):
        panel = LibraryPanel()
        qtbot.addWidget(panel)
        
        # 3. Trigger Refresh
        # (Assuming panel refreshes on init, but we force it)
        if hasattr(panel, 'refresh'):
            panel.refresh()
            
    # 4. Assertions
    # Check if tree widget has our Mock Data
    # (Implementation dependent, but checking for text existence is robust)
    items = panel.findChildren(object) # Search generic children or inspect tree directly
    
    # Better: Inspect the QTreeWidget
    tree = panel.tree # Assuming standard property name from spec
    assert tree.topLevelItemCount() > 0, "Library Tree is empty"
    
    found = False
    for i in range(tree.topLevelItemCount()):
        item = tree.topLevelItem(i)
        # Search children of categories
        for j in range(item.childCount()):
            sub = item.child(j)
            if "TEST_PART_A" in sub.text(0):
                found = True
                break
    
    assert found, \
        "VIOLATION: LibraryPanel ignored API data! It likely tried loading from disk (or failed silently)."
