import pytest
from ui.layout_manager import LayoutManager
from PySide6.QtWidgets import QMainWindow, QMenuBar

def test_menubar_generation(qtbot, tmp_path):
    """PH5-SHELL.1: Should generate QMenuBar from YAML."""
    # Create Mock Config
    config_file = tmp_path / "layout.yaml"
    config_file.write_text("""
    menubar:
      - label: "File"
        items:
          - command: "file.new"
      - label: "View"
        items:
          - command: "view.zoom_all"
    """)
    
    # Initialize Manager
    win = QMainWindow()
    manager = LayoutManager(config_path=str(config_file))
    
    # Generate Menu
    menubar = manager.create_menubar(win)
    win.setMenuBar(menubar)
    
    assert isinstance(menubar, QMenuBar)
    actions = menubar.actions()
    assert len(actions) == 2
    assert actions[0].text() == "File"
    assert actions[1].text() == "View"