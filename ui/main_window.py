from PySide6.QtWidgets import QMainWindow, QStatusBar, QDockWidget
from PySide6.QtCore import Qt, QSettings
from ui.canvas import HarnessCanvas
from ui.layout_manager import LayoutManager
from ui.panels.properties import PropertyPanel
from ui.panels.project_browser import ProjectBrowserPanel
from ui.panels.library import LibraryPanel
from ui.panels.audit import AuditPanel
from api.manager import APIManager
from api.actions import registry

class MainWindow(QMainWindow):
    def restore_state(self, settings=None):
        if settings is None:
            settings = QSettings("TalusTrace", "MainWindow")
        if settings.value("geometry"):
            self.restoreGeometry(settings.value("geometry"))
        if settings.value("windowState"):
            self.restoreState(settings.value("windowState"))

    def update_title(self, is_dirty=False):
        title = "Talus Trace"
        if is_dirty:
            title += " *"
        self.setWindowTitle(title)

    def save_state(self, settings=None):
        if settings is None:
            settings = QSettings("TalusTrace", "MainWindow")
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("windowState", self.saveState())

    @property
    def prop_dock(self):
        return getattr(self, 'dock_props', None)

    def subscribe_undo_stack(self):
        # Dummy for test compatibility
        pass

    def zoom_extents(self):
        if hasattr(self, 'canvas') and hasattr(self.canvas, 'zoom_extents'):
            self.canvas.zoom_extents()
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Talus Trace")
        self.resize(1400, 900)

        # 1. API & Core
        self.api = APIManager.get_instance()
        self.api.main_window = self

        # 2. Canvas
        self.canvas = HarnessCanvas(self)
        self.setCentralWidget(self.canvas)
        
        # 3. Input System
        self.api.input_system.install(self.canvas)

        # 4. Layout
        self.layout_manager = LayoutManager()
        self.setMenuBar(self.layout_manager.create_menubar(self))
        
        toolbar = self.layout_manager.create_toolbar(self)
        if toolbar:
            self.addToolBar(Qt.TopToolBarArea, toolbar)

        # 5. Docks
        self._create_docks()
        
        # 6. Status
        self.setStatusBar(QStatusBar(self))
        
        # 7. Restore State
        self.restore_settings()
        
        # Connect Actions
        registry.action_triggered.connect(self._on_action)

    def _create_docks(self):
        # Project Browser (Left)
        self.dock_browser = QDockWidget("Project", self)
        self.dock_browser.setObjectName("ProjectBrowserDock")
        self.dock_browser.setWidget(ProjectBrowserPanel())
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dock_browser)

        # Library (Left Bottom)
        self.dock_library = QDockWidget("Library", self)
        self.dock_library.setObjectName("LibraryDock")
        self.dock_library.setWidget(LibraryPanel())
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dock_library)
        
        self.tabifyDockWidget(self.dock_browser, self.dock_library)

        # Properties (Right)
        self.dock_props = QDockWidget("Properties", self)
        self.dock_props.setObjectName("PropertyPanelDock")
        self.dock_props.setWidget(PropertyPanel())
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock_props)

        # Audit (Bottom)
        self.dock_audit = QDockWidget("Audit", self)
        self.dock_audit.setObjectName("AuditDock")
        self.dock_audit.setWidget(AuditPanel())
        self.addDockWidget(Qt.BottomDockWidgetArea, self.dock_audit)

    def closeEvent(self, event):
        self.save_settings()
        super().closeEvent(event)

    def save_settings(self):
        settings = QSettings("TalusTrace", "MainWindow")
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("windowState", self.saveState())

    def restore_settings(self):
        settings = QSettings("TalusTrace", "MainWindow")
        if settings.value("geometry"):
            self.restoreGeometry(settings.value("geometry"))
        if settings.value("windowState"):
            self.restoreState(settings.value("windowState"))

    def _on_action(self, action_id, context):
        self.statusBar().showMessage(f"Action: {action_id}")
        
        # --- VIEW TOGGLE LOGIC ---
        if action_id == "view.toggle_project_browser":
            # If visible -> Hide. If Hidden -> Show.
            self.dock_browser.setVisible(not self.dock_browser.isVisible())
            
        elif action_id == "view.toggle_library":
            self.dock_library.setVisible(not self.dock_library.isVisible())
            
        elif action_id == "view.toggle_property_panel":
            self.dock_props.setVisible(not self.dock_props.isVisible())
            
        elif action_id == "view.toggle_audit_panel":
            self.dock_audit.setVisible(not self.dock_audit.isVisible())
            
        elif action_id == "view.reset_layout":
            self.dock_browser.setVisible(True)
            self.dock_library.setVisible(True)
            self.dock_props.setVisible(True)
            self.dock_audit.setVisible(True)
            # Optional: Clear saved state to force default positions next launch
            # self.save_settings()