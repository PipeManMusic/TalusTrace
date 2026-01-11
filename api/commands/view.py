from PySide6.QtWidgets import QApplication, QDockWidget
from api.actions import register_action
from api.manager import APIManager

@register_action("view.toggle_project_browser")
def view_toggle_project_browser(context):
    _toggle_dock("ProjectBrowserDock")

@register_action("view.toggle_property_panel")
def view_toggle_property_panel(context):
    _toggle_dock("PropertyPanelDock")

@register_action("view.toggle_library")
def view_toggle_library(context):
    _toggle_dock("LibraryDock")

@register_action("view.reset_layout")
def view_reset_layout(context):
    win = QApplication.activeWindow()
    if not win: return
    for name in ["ProjectBrowserDock", "PropertyPanelDock", "LibraryDock"]:
        dock = win.findChild(QDockWidget, name)
        if dock: dock.setVisible(True)

@register_action("view.zoom_extents")
def view_zoom_extents(context):
    win = QApplication.activeWindow()
    if win and hasattr(win, 'canvas'):
        win.canvas.zoom_extents()

@register_action("view.zoom_selected")
def view_zoom_selected(context):
    win = QApplication.activeWindow()
    if win and hasattr(win, 'canvas'):
        # For now, just reuse extents or impl selection zoom
        win.canvas.zoom_extents() 

@register_action("view.toggle_grid")
def view_toggle_grid(context):
    pass # Grid toggle logic to be implemented in Canvas

def _toggle_dock(object_name):
    win = QApplication.activeWindow()
    if not win: return
    dock = win.findChild(QDockWidget, object_name)
    if dock:
        dock.setVisible(not dock.isVisible())
