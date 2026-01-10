from PySide6.QtWidgets import QFileDialog, QApplication
from api.actions import register_action
from api.manager import APIManager
from infra.context import ProjectContext

@register_action("file.new")
def file_new(context):
    api = APIManager.get_instance()
    api.context = ProjectContext()
    api.context.undo_stack.clear()
    api.context.current_file = None
    api.context.dirty = False
    
    window = QApplication.activeWindow()
    if window and hasattr(window, 'canvas'):
        window.canvas.load_harness(api.context.harness)
    print(">> COMMAND: New File executed.")

@register_action("file.open")
def file_open(context):
    api = APIManager.get_instance()
    path, _ = QFileDialog.getOpenFileName(None, "Open Harness File", "", "YAML Files (*.yaml *.yml)")
    if path:
        api.context = ProjectContext()
        api.context.load(path)
        api.context.current_file = path
        api.context.dirty = False

@register_action("file.save")
def file_save(context):
    api = APIManager.get_instance()
    ctx = api.context
    path = getattr(ctx, 'current_file', None)
    if not path:
        path, _ = QFileDialog.getSaveFileName(None, "Save Harness File", "harness.yaml", "YAML Files (*.yaml *.yml)")
        if not path: return
    ctx.save_as(path)

@register_action("file.save_as")
def file_save_as(context):
    api = APIManager.get_instance()
    ctx = api.context
    path, _ = QFileDialog.getSaveFileName(None, "Save Harness File As", "harness.yaml", "YAML Files (*.yaml *.yml)")
    if not path:
        return
    ctx.save_as(path)
    ctx.current_file = path

@register_action("file.exit")
def file_exit(context):
    QApplication.quit()

@register_action("file.export_bom")
def file_export_bom(context):
    from infra.bom import BOMGenerator
    path, _ = QFileDialog.getSaveFileName(None, "Export BOM", "bom.csv", "CSV Files (*.csv)")
    if path:
        gen = BOMGenerator(APIManager.get_instance().context)
        gen.generate_bom(path)
