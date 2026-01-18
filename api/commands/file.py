from PySide6.QtWidgets import QFileDialog, QApplication, QMessageBox
from api.actions import register_action
from api.manager import APIManager
# FIXED: Import 'Context' instead of 'ProjectContext'
from infra.context import Context 
import yaml

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

    # FIXED: Use new class name
    api.context = Context()
    api.context.undo_stack.clear()
    api.dispatch("model_changed", {"action": "new"})

@register_action("file.save")
def file_save(context):
    path, _ = QFileDialog.getSaveFileName(None, "Save Harness", "harness.yaml", "YAML (*.yaml)")
    if not path: return
    
    api = APIManager.get_instance()
    try:
        api.context.save_as(path)
        # ...removed debug print...
    except Exception as e:
        # ...removed debug print...
        pass

@register_action("file.open")
def file_open(context):
    path, _ = QFileDialog.getOpenFileName(None, "Open Harness", "", "YAML (*.yaml)")
    if not path: return
    
    api = APIManager.get_instance()
    try:
        api.context.load(path)
        api.dispatch("model_changed", {"action": "load"})
        # ...removed debug print...
    except Exception as e:
        # ...removed debug print...
        pass

@register_action("file.export_bom")
def file_export_bom(context):
    pass

@register_action("file.export_wirelist")
def file_export_wirelist(context):
    pass

@register_action("file.exit")
def file_exit(context):
    QApplication.quit()