from PySide6.QtWidgets import QApplication, QDockWidget
from api.actions import register_action

@register_action("view.toggle_project_browser")
def view_toggle_project_browser(context):
    window = QApplication.activeWindow()
    if not window: return
    
    dock = window.findChild(QDockWidget, "ProjectBrowserDock")
    if dock:
        dock.setVisible(not dock.isVisible())

@register_action("view.toggle_property_panel")
def view_toggle_property_panel(context):
    window = QApplication.activeWindow()
    if not window: return
    
    dock = window.findChild(QDockWidget, "PropertyPanelDock")
    if dock:
        dock.setVisible(not dock.isVisible())

@register_action("view.reset_layout")
def view_reset_layout(context):
    window = QApplication.activeWindow()
    if not window: return
    
    for name in ["ProjectBrowserDock", "PropertyPanelDock"]:
        dock = window.findChild(QDockWidget, name)
        if dock:
            dock.setVisible(True)
