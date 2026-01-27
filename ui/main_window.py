"""
Main application window for Talus Trace UI.

Handles window setup, toolbars, menus, panels, and state persistence.
"""
from PySide6.QtWidgets import QMainWindow, QDockWidget, QMessageBox
from PySide6.QtCore import QSettings
from api.manager import APIManager
from ui.canvas import HarnessCanvas
from ui.layout_manager import LayoutManager
from ui.panels.project_browser import ProjectBrowser
from ui.panels.library import LibraryPanel
from ui.panels.properties import PropertiesPanel
from ui.panels.audit import AuditPanel
# --- FIX: Import the Dialog ---
from ui.dialogs.device_wizard import DeviceWizard

class MainWindow(QMainWindow):
    """Main application window for Talus Trace, managing UI layout and state."""
    def register_toolbar_commands(self):
        """Register toolbar command actions for tools and undo/redo."""
        from api.actions import register_action

        # --- Existing Tools ---
        register_action("tool.move")(lambda ctx=None: self.api.tool_manager.set_tool("move"))
        register_action("tool.add_generic_device")(lambda ctx=None: self.api.tool_manager.set_tool("placement"))

        # Register device wizard, undo, redo with correct context handling
        register_action("device.create_wizard")(lambda ctx: ctx.activate_device_wizard() if hasattr(ctx, "activate_device_wizard") else None)
        register_action("edit.undo")(lambda ctx=None: self.api.context.undo_stack.undo())
        register_action("edit.redo")(lambda ctx=None: self.api.context.undo_stack.redo())
        # Stub for coverage
        register_action("tool.measure")(lambda ctx: None)

    def activate_device_wizard(self):
        """Open the device wizard dialog and handle completion."""
        dialog = DeviceWizard(self)
        if dialog.exec():
            print("[MainWindow] Device Wizard completed successfully.")
            if hasattr(self, 'library_panel'):
                self.library_panel.refresh()

    def undo(self):
        """Undo the last action using the context's undo stack."""
        if getattr(self, 'api', None) and getattr(self.api, 'context', None) and hasattr(self.api.context, 'undo_stack'):
            self.api.context.undo_stack.undo()

    def redo(self):
        """Redo the last undone action using the context's undo stack."""
        if getattr(self, 'api', None) and getattr(self.api, 'context', None) and hasattr(self.api.context, 'undo_stack'):
            self.api.context.undo_stack.redo()

    def register_panel_toggles(self):
        """Register actions to toggle visibility of dock panels."""
        from api.actions import register_action
        # Helper to toggle dock widget visibility
        def toggle_dock(dock):
            """Toggle the visibility of a given dock widget."""
            if dock:
                dock.setVisible(not dock.isVisible())
        register_action("view.toggle_project_browser")(lambda ctx: toggle_dock(self.project_browser_dock))
        register_action("view.toggle_property_panel")(lambda ctx: toggle_dock(self.properties_panel_dock))
        register_action("view.toggle_library")(lambda ctx: toggle_dock(self.library_panel_dock))
        register_action("view.toggle_audit_panel")(lambda ctx: toggle_dock(self.audit_panel_dock))

    def __init__(self, parent=None):
        """Initialize the main window, UI layout, panels, and restore state."""
        super().__init__(parent)
        from ui.i18n import I18N
        self.setWindowTitle(I18N.get('window_title'))
        self.resize(1400, 900)

        # 1. API & Core
        self.api = APIManager.get_instance()
        self.api.main_window = self

        # 2. Canvas (Central Widget)
        # CRITICAL: Must be set BEFORE layout manager to ensure it exists
        self.canvas = HarnessCanvas(self)
        self.setCentralWidget(self.canvas)
        
        # Set APIManager.scene and APIManager.view for tool compatibility
        self.api.scene = self.canvas.scene
        self.api.view = self.canvas
        # Load the current harness into the canvas
        self.canvas.load_harness(self.api.context.harness)

        # 3. Input System (Wired in app.py, now installed here)
        # Always install InputSystem on the canvas viewport for robust mouse event handling
        if self.api.input_system:
            self.api.input_system.install(self.canvas.viewport())

        # 4. Menus & Toolbars
        import api.commands.file
        self.layout_manager = LayoutManager()
        self.setMenuBar(self.layout_manager.create_menubar(self))

        toolbar = self.layout_manager.create_toolbar(self)
        self.addToolBar(toolbar)

        # --- FIX 3: Wire up Context Menu ---
        from ui.context_menu_manager import ContextMenuManager
        from api.actions import actions_map  # Use the global actions_map
        self.context_menu_manager = ContextMenuManager(self.layout_manager.config, actions_map)
        
        # API will call context_menu_manager.show_context_menu via main_window.context_menu_manager

        # 5. Panels (Dock Widgets)
        self._create_panels()
        self.register_panel_toggles()
        self.register_toolbar_commands()

        # 6. Restore State (if saved)
        self._restore_state()

    def restore_state(self, settings=None):
        """Restore window geometry and state from QSettings or provided settings."""
        from PySide6.QtCore import QSettings
        if settings is None:
            settings = QSettings("TalusTrace", "MainWindow")
        if settings.value("geometry"):
            self.restoreGeometry(settings.value("geometry"))
        if settings.value("windowState"):
            self.restoreState(settings.value("windowState"))

    def update_title(self, is_dirty=False):
        """Update the window title, appending '*' if the state is dirty."""
        from ui.i18n import I18N
        title = I18N.get('window_title')
        if is_dirty:
            title += " *"
        self.setWindowTitle(title)

    def save_state(self, settings=None):
        """Save window geometry and state to QSettings or provided settings."""
        from PySide6.QtCore import QSettings
        if settings is None:
            settings = QSettings("TalusTrace", "MainWindow")
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("windowState", self.saveState())

    @property
    def prop_dock(self):
        """Return the property dock widget for the main window."""
        return getattr(self, 'properties_panel_dock', None)

    def _create_panels(self):
        """Create and add all dock panels (project browser, library, properties, audit)."""
        from PySide6.QtCore import Qt
        # Project Browser (Left)
        self.project_browser = ProjectBrowser(self)
        self.project_browser_dock = QDockWidget("Project Browser", self)
        self.project_browser_dock.setObjectName("ProjectBrowserDock")
        self.project_browser_dock.setWidget(self.project_browser)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.project_browser_dock)

        # Library (Left, Tabbed)
        self.library_panel = LibraryPanel(self)
        self.library_panel_dock = QDockWidget("Library", self)
        self.library_panel_dock.setObjectName("LibraryPanelDock")
        self.library_panel_dock.setWidget(self.library_panel)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.library_panel_dock)
        self.tabifyDockWidget(self.project_browser_dock, self.library_panel_dock)

        # Properties (Right)
        self.properties_panel = PropertiesPanel(self)
        self.properties_panel_dock = QDockWidget("Properties", self)
        self.properties_panel_dock.setObjectName("PropertiesPanelDock")
        self.properties_panel_dock.setWidget(self.properties_panel)
        self.addDockWidget(Qt.RightDockWidgetArea, self.properties_panel_dock)

        # Audit (Bottom)
        self.audit_panel = AuditPanel(self)
        self.audit_panel_dock = QDockWidget("Audit", self)
        self.audit_panel_dock.setObjectName("AuditPanelDock")
        self.audit_panel_dock.setWidget(self.audit_panel)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.audit_panel_dock)

    def _restore_state(self):
        """Restore window geometry and state from QSettings."""
        settings = QSettings("TalusTrace", "App")
        if settings.value("geometry"):
            self.restoreGeometry(settings.value("geometry"))
        if settings.value("windowState"):
            self.restoreState(settings.value("windowState"))

    def closeEvent(self, event):
        """Save window state on close and call the base closeEvent."""
        settings = QSettings("TalusTrace", "App")
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("windowState", self.saveState())
        super().closeEvent(event)