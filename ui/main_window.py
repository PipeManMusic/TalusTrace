from PySide6.QtWidgets import QMainWindow, QStatusBar, QDockWidget
from PySide6.QtCore import Qt
from ui.canvas import HarnessCanvas
from ui.input_system import InputSystem
from ui.layout_manager import LayoutManager
from ui.panels.properties import PropertyPanel # <--- NEW
from api.actions import registry
from api.manager import APIManager
from ui.panels.library import LibraryPanel

from ui.commands import CommandStack
command_stack = CommandStack()  # Global stack for UI commands

class MainWindow(QMainWindow):

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

        # 3. Toolbar
        self.layout_manager = LayoutManager()
        self.toolbar = self.layout_manager.create_toolbar(self)
        if self.toolbar:
            self.addToolBar(self.toolbar)

        # 4. Property Panel (Dock)
        self.prop_dock = QDockWidget("Properties", self)
        self.prop_panel = PropertyPanel()
        self.prop_dock.setWidget(self.prop_panel)
        self.prop_dock.setAllowedAreas(Qt.RightDockWidgetArea | Qt.LeftDockWidgetArea)
        self.addDockWidget(Qt.RightDockWidgetArea, self.prop_dock)

        # 4b. Library Panel (Dock)
        self.lib_dock = QDockWidget("Library", self)
        self.lib_panel = LibraryPanel() # Uses defaults
        self.lib_dock.setWidget(self.lib_panel)
        self.lib_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.lib_dock)

        # 5. Status Bar
        self.setStatusBar(QStatusBar(self))
        registry.action_triggered.connect(self._on_action_triggered)

        # Show git hash on startup
        self._show_git_hash()

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