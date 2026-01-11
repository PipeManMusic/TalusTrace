from PySide6.QtWidgets import QFileDialog, QApplication, QMessageBox
from api.actions import register_action
from api.manager import APIManager
from infra.context import ProjectContext

@register_action("file.new")
def file_new(context):
    api = APIManager.get_instance()
    
    if api.context.dirty:
        res = QMessageBox.question(
            None, "Unsaved Changes", 
            "You have unsaved changes. Discard them?",
            QMessageBox.Yes | QMessageBox.No
        )
        if res != QMessageBox.Yes:
            return

    api.context = ProjectContext()
    api.context.undo_stack.clear()
    api.context.current_file = None
    api.context.dirty = False
    
    api.dispatch("model_changed", {"action": "new"})
    window = QApplication.activeWindow()
    if window and hasattr(window, 'canvas'):
        window.canvas.load_harness(api.context.harness)

@register_action("file.open")
def file_open(context):
    api = APIManager.get_instance()
    path, _ = QFileDialog.getOpenFileName(None, "Open Harness", "", "YAML (*.yaml)")
    if path:
        api.context = ProjectContext()
        api.context.load(path)
        api.context.current_file = path
        api.context.dirty = False
        api.dispatch("model_changed", {"action": "open"})
        
        win = QApplication.activeWindow()
        if win: win.canvas.load_harness(api.context.harness)

@register_action("file.save")
def file_save(context):
    api = APIManager.get_instance()
    path = getattr(api.context, 'current_file', None)
    if not path:
        path, _ = QFileDialog.getSaveFileName(None, "Save Harness", "harness.yaml", "YAML (*.yaml)")
        if not path: return
    api.context.save_as(path)
    api.context.current_file = path
    api.context.dirty = False

@register_action("file.exit")
def file_exit(context):
    QApplication.quit()

@register_action("file.export_bom")
def file_export_bom(context):
    print(">> Export BOM stub")

@register_action("file.export_wirelist")
def file_export_wirelist(context):
    print(">> Export Wirelist stub")
