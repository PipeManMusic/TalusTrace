import pytest
from infra.context import ProjectContext
from ui.main_window import MainWindow

def test_dirty_flag_logic():
    """PH5-SHELL.4: Modifying context should set is_dirty."""
    ctx = ProjectContext()
    assert ctx.is_dirty is False
    
    ctx.mark_dirty()
    assert ctx.is_dirty is True
    
    ctx.mark_clean()
    assert ctx.is_dirty is False

def test_window_title_update(qtbot):
    """PH5-SHELL.4: Window title should show '*' when dirty."""
    win = MainWindow()
    qtbot.add_widget(win)
    
    # Default State
    assert "*" not in win.windowTitle()
    
    # Dirty State
    win.update_title(is_dirty=True)
    assert "*" in win.windowTitle()
    
    # Clean State
    win.update_title(is_dirty=False)
    assert "*" not in win.windowTitle()