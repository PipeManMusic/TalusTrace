from PySide6.QtWidgets import QMainWindow, QStatusBar, QDockWidget
from PySide6.QtCore import Qt
from ui.canvas import HarnessCanvas
from ui.input_system import InputSystem
from ui.layout_manager import LayoutManager
from ui.panels.properties import PropertyPanel
from api.actions import registry
from api.manager import APIManager
from ui.panels.library import LibraryPanel

from ui.commands import CommandStack
command_stack = CommandStack()  # Global stack for UI commands

class MainWindow(QMainWindow):

    def save_state(self, settings):
        """Saves window geometry and state to QSettings."""
        settings.setValue("geometry", self.saveGeometry())
        settings.setValue("windowState", self.saveState())
        # Explicitly save dock sizes
        settings.setValue("propDockSize", self.prop_dock.size())
        settings.setValue("libDockSize", self.lib_dock.size())

    def restore_state(self, settings):
        """Restores window geometry and state from QSettings."""
        if settings.contains("geometry"):
            self.restoreGeometry(settings.value("geometry"))
        if settings.contains("windowState"):
            self.restoreState(settings.value("windowState"))
        # Explicitly restore dock sizes
        if settings.contains("propDockSize"):
            self.prop_dock.resize(settings.value("propDockSize"))
        if settings.contains("libDockSize"):
            self.lib_dock.resize(settings.value("libDockSize"))

    def update_title(self, is_dirty: bool):
        base = "Talus Trace"
        if is_dirty:
            self.setWindowTitle(f"*{base}")
        else:
            self.setWindowTitle(base)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Talus Trace")
        self.resize(1280, 800)

        # 1. Central Canvas
        self.canvas = HarnessCanvas(self)
        self.setCentralWidget(self.canvas)

        # 2. Input System
        self.input_system = InputSystem()
        self.input_system.install()
        APIManager.get_instance().input_system = self.input_system

        # 3. Layout Resources (Toolbar & Menubar)
        self.layout_manager = LayoutManager()
        
        # PH5-CLN.1: Initialize Menubar from YAML config
        # This call creates the QMenuBar and attaches it to the QMainWindow
        self.setMenuBar(self.layout_manager.create_menubar(self))

        # Initialize Toolbar from YAML config
        self.toolbar = self.layout_manager.create_toolbar(self)
        if self.toolbar:
            self.toolbar.setObjectName("MainToolbar")
            self.addToolBar(self.toolbar)

        # 4. Property Panel (Dock)
        self.prop_dock = QDockWidget("Properties", self)
        self.prop_dock.setObjectName("PropertiesDock")
        self.prop_panel = PropertyPanel()
        self.prop_dock.setWidget(self.prop_panel)
        self.prop_dock.setAllowedAreas(Qt.RightDockWidgetArea | Qt.LeftDockWidgetArea)
        self.addDockWidget(Qt.RightDockWidgetArea, self.prop_dock)

        # 4b. Library Panel (Dock)
        self.lib_dock = QDockWidget("Library", self)
        self.lib_dock.setObjectName("LibraryDock")
        self.lib_panel = LibraryPanel() # Uses defaults
        self.lib_dock.setWidget(self.lib_panel)
        self.lib_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.lib_dock)

        # 5. Status Bar
        self.setStatusBar(QStatusBar(self))
        registry.action_triggered.connect(self._on_action_triggered)

        # Show git hash on startup
        self._show_git_hash()

    def subscribe_undo_stack(self):
        api = APIManager.get_instance()
        api.context.undo_stack.subscribe(self._on_undo_stack_event)

    def _on_undo_stack_event(self, event_type):
        # Refresh canvas on undo/redo
        api = APIManager.get_instance()
        self.canvas.load_harness(api.context.harness)

    def _on_undo_stack_event(self, event_type):
        # Refresh canvas on undo/redo
        api = APIManager.get_instance()
        self.canvas.load_harness(api.context.harness)

    def _show_git_hash(self):
        import subprocess
        try:
            git_hash = subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], cwd=".").decode().strip()
            self.statusBar().showMessage(f"Git: {git_hash}")
        except Exception:
            self.statusBar().showMessage("Git: unknown")

    def show_coordinates(self, x, y):
        self.statusBar().showMessage(f"Coordinates: ({x:.2f}, {y:.2f})")

    def show_tool_hint(self, hint):
        self.statusBar().showMessage(f"Hint: {hint}")

    def _on_action_triggered(self, action_id, context):
        self.statusBar().showMessage(f"Action Triggered: {action_id}")
        # Toggle Panel Logic (Command Handler)
        if action_id == "view.toggle_props":
            if self.prop_dock.isVisible():
                self.prop_dock.hide()
            else:
                self.prop_dock.show()