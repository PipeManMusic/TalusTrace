"""
View-related command actions for Talus Trace.
Provides UI toggling, layout reset, and zoom commands.
"""
from PySide6.QtWidgets import QApplication, QDockWidget
from api.actions import register_action
from api.manager import APIManager

def _toggle_dock(object_name):
    """
    Toggle the visibility of a dock widget by object name.
    Args:
        object_name: The name of the dock widget to toggle.
    """
    win = QApplication.activeWindow()
    if not win: return
    
    dock = win.findChild(QDockWidget, object_name)
    if dock:
        dock.setVisible(not dock.isVisible())

@register_action("view.toggle_project_browser")
def view_toggle_browser(context):
    """
    Toggle the visibility of the project browser dock.
    Args:
        context: The action context.
    """
    pass

@register_action("view.toggle_library")
def view_toggle_library(context):
    """
    Toggle the visibility of the library dock.
    Args:
        context: The action context.
    """
    pass

@register_action("view.toggle_property_panel")
def view_toggle_props(context):
    """
    Toggle the visibility of the property panel dock.
    Args:
        context: The action context.
    """
    pass

@register_action("view.toggle_audit_panel")
def view_toggle_audit(context):
    """
    Toggle the visibility of the audit panel dock.
    Args:
        context: The action context.
    """
    pass

@register_action("view.reset_layout")
def view_reset_layout(context):
    """
    Reset the layout of all main dock widgets and canvas zoom.
    Args:
        context: The action context.
    """
    win = QApplication.activeWindow()
    if not win: return
    # Basic reset logic (could be expanded)
    for name in ["ProjectBrowserDock", "PropertyPanelDock", "LibraryDock"]:
        dock = win.findChild(QDockWidget, name)
        if dock: dock.setVisible(True)
    
    # Reset Zoom
    if hasattr(win, 'canvas'):
        win.canvas.resetTransform()

@register_action("view.zoom_extents")
def view_zoom_extents(context):
    """
    Zoom the canvas to show all contents.
    Args:
        context: The action context.
    """
    win = QApplication.activeWindow()
    if win and hasattr(win, 'canvas'):
        win.canvas.zoom_extents()

@register_action("view.zoom_selected")
def view_zoom_selected(context):
    """
    Zoom the canvas to show the selected items.
    Args:
        context: The action context.
    """
    pass # Placeholder
