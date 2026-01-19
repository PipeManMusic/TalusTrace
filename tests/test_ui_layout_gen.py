import pytest
from ui.layout_manager import LayoutManager
from PySide6.QtWidgets import QMainWindow, QMenuBar, QMenu

# @pytest.mark.skip(reason="Menu logic pending refactor") # REMOVED
def test_menubar_generation(qtbot, tmp_path):
    """PH5-SHELL.1: Should generate QMenuBar from YAML."""
    # Create Mock Config
    config_file = tmp_path / "layout.yaml"
    config_file.write_text("""
    menubar:
      - label: "File"
        items:
          - command: "file.new"
            label: "New"
      - label: "View"
        items:
          - command: "view.zoom_all"
            label: "Zoom All"
    """)
    
    # Initialize Manager
    win = QMainWindow()
    manager = LayoutManager(config_path=str(config_file))
    
    # Generate Menu
    menubar = manager.create_menubar(win)
    win.setMenuBar(menubar)
    
    assert isinstance(menubar, QMenuBar)
    actions = menubar.actions()
    # QMenuBar actions correspond to the top-level menus (File, View)
    assert len(actions) == 2
    assert actions[0].text() == "File"
    assert actions[1].text() == "View"
    
    # Verify Submenus
    # Access the QMenu associated with the top-level action
    file_menu = actions[0].menu()
    assert file_menu is not None
    
    sub_actions = file_menu.actions()
    assert len(sub_actions) == 1
    assert sub_actions[0].text() == "New"
    assert sub_actions[0].data() == "file.new"