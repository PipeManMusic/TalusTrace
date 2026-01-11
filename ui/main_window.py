from PySide6.QtWidgets import QMainWindow, QStatusBar, QDockWidget
from PySide6.QtCore import Qt
from ui.canvas import HarnessCanvas
from ui.input_system import InputSystem
from ui.layout_manager import LayoutManager
from ui.panels.properties import PropertyPanel
from ui.panels.project_browser import ProjectBrowser
from ui.panels.library import LibraryPanel
from api.actions import registry
from api.manager import APIManager

class MainWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Talus Trace")
        self.resize(1400, 900)

        # 1. API & Core
        api = APIManager.get_instance()
        api.main_window = self

        # 2. Canvas
        self.canvas = HarnessCanvas(self)
        self.setCentralWidget(self.canvas)

        # 3. Input & Layout
        self.input_system = InputSystem()
        self.input_system.install()
        
        # Use LayoutManager to read YAML and build Menus/Toolbars
        self.layout_manager = LayoutManager()
        self.setMenuBar(self.layout_manager.create_menubar(self))
        self.addToolBar(self.layout_manager.create_toolbar(self))

        # 4. Docks
        self._create_docks()
        
        # 5. Status
        self.setStatusBar(QStatusBar(self))
        self._show_git_hash()
        
        registry.action_triggered.connect(self._on_action)

    def _create_docks(self):
        # Left: Browser & Library
        self.dock_browser = QDockWidget("Project", self)
        self.dock_browser.setObjectName("ProjectBrowserDock")
        self.dock_browser.setWidget(ProjectBrowser())
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dock_browser)

        self.dock_library = QDockWidget("Library", self)
        self.dock_library.setObjectName("LibraryDock")
        self.dock_library.setWidget(LibraryPanel())
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dock_library)
        
        self.tabifyDockWidget(self.dock_browser, self.dock_library)

        # Right: Properties
        self.dock_props = QDockWidget("Properties", self)
        self.dock_props.setObjectName("PropertyPanelDock")
        self.dock_props.setWidget(PropertyPanel())
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock_props)

    def _on_action(self, action_id, context):
        self.statusBar().showMessage(f"Action: {action_id}")
        
        # FIX: Handle View Toggles based on YAML command IDs
        if action_id == "view.toggle_library":
            self.dock_library.setVisible(not self.dock_library.isVisible())
        elif action_id == "view.toggle_project_browser":
            self.dock_browser.setVisible(not self.dock_browser.isVisible())
        elif action_id == "view.toggle_property_panel":
            self.dock_props.setVisible(not self.dock_props.isVisible())
        elif action_id == "view.reset_layout":
            self.dock_browser.show()
            self.dock_library.show()
            self.dock_props.show()

    def _show_git_hash(self):
        try:
            import subprocess
            h = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"]).decode().strip()
            self.statusBar().showMessage(f"Git: {h}")
        except: pass

    def closeEvent(self, e): super().closeEvent(e)
