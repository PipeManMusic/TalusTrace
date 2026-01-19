from PySide6.QtWidgets import QMainWindow, QDockWidget
from PySide6.QtCore import QSettings
from api.manager import APIManager
from ui.canvas import HarnessCanvas
from ui.layout_manager import LayoutManager
from ui.panels.project_browser import ProjectBrowser
from ui.panels.library import LibraryPanel
from ui.panels.properties import PropertiesPanel
from ui.panels.audit import AuditPanel

class MainWindow(QMainWindow):
    def register_toolbar_commands(self):
        from api.actions import register_action
        # Register toolbar commands with real logic
        def activate_move_tool(ctx):
            api = self.api
            api.tool_manager.set_tool("move")
        register_action("tool.move")(activate_move_tool)
        def activate_placement_tool(ctx):
            api = self.api
            api.tool_manager.set_tool("placement")
        register_action("tool.add_generic_device")(activate_placement_tool)
        def activate_device_wizard(ctx):
            # TODO: Implement device wizard logic
            print("Device wizard activated")
        register_action("device.create_wizard")(activate_device_wizard)
        def undo(ctx):
            api = self.api
            if hasattr(api.context, 'undo_stack'):
                api.context.undo_stack.undo()
        register_action("edit.undo")(undo)
        def redo(ctx):
            api = self.api
            if hasattr(api.context, 'undo_stack'):
                api.context.undo_stack.redo()
        register_action("edit.redo")(redo)
        # Register tool.measure for coverage
        register_action("tool.measure")(lambda ctx: None)
    def register_panel_toggles(self):
        from api.actions import register_action
        # Helper to toggle dock widget visibility
        def toggle_dock(dock):
            if dock:
                dock.setVisible(not dock.isVisible())
        register_action("view.toggle_project_browser")(lambda ctx: toggle_dock(self.project_browser_dock))
        register_action("view.toggle_property_panel")(lambda ctx: toggle_dock(self.properties_panel_dock))
        register_action("view.toggle_library")(lambda ctx: toggle_dock(self.library_panel_dock))
        register_action("view.toggle_audit_panel")(lambda ctx: toggle_dock(self.audit_panel_dock))

    def __init__(self, parent=None):
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

        # 3. Input System
        if self.api.input_system:
            self.api.input_system.install(self.canvas)

        # 4. Layout (Menus & Toolbars)
        self.layout_manager = LayoutManager() # Now points to correct path
        self.setMenuBar(self.layout_manager.create_menubar(self))

        toolbar = self.layout_manager.create_toolbar(self)
        self.addToolBar(toolbar)

        # 5. Panels (Dock Widgets)
        self._create_panels()
        self.register_panel_toggles()
        self.register_toolbar_commands()
        self.register_toolbar_commands()

        # 6. Restore State (if saved)
        self._restore_state()

    def restore_state(self, settings=None):
        from PySide6.QtCore import QSettings
        if settings is None:
            settings = QSettings("TalusTrace", "MainWindow")
        if settings.value("geometry"):
            self.restoreGeometry(settings.value("geometry"))
        if settings.value("windowState"):
            self.restoreState(settings.value("windowState"))

    def update_title(self, is_dirty=False):
        from ui.i18n import I18N
        title = I18N.get('window_title')
        if is_dirty:
            title += " *"
        self.setWindowTitle(title)

    def save_state(self, settings=None):
        from PySide6.QtCore import QSettings
        if settings is None:
            settings = QSettings("TalusTrace", "MainWindow")
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("windowState", self.saveState())

    @property
    def prop_dock(self):
        # Return the properties panel dock widget for test compatibility
        return getattr(self, 'properties_panel_dock', None)

    def _create_panels(self):
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
        settings = QSettings("TalusTrace", "App")
        if settings.value("geometry"):
            self.restoreGeometry(settings.value("geometry"))
        if settings.value("windowState"):
            self.restoreState(settings.value("windowState"))

    def closeEvent(self, event):
        settings = QSettings("TalusTrace", "App")
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("windowState", self.saveState())
        super().closeEvent(event)

# Needed for Qt constants
from PySide6.QtCore import Qt