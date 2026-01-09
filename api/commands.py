import uuid
from core.device import Device
from core.pin import Pin, Side
from api.actions import register_action
from api.manager import APIManager
from PySide6.QtWidgets import QFileDialog, QApplication
from core.device import Device
from core.wire import Wire
from ui.dialogs.device_wizard import DeviceWizard
from tools.move_tool import MoveTool

# --- Place Generic Device ---
@register_action("tool.add_generic_device")
def tool_add_generic_device(context):
    """Activates the placement tool via the ToolManager."""
    api = APIManager.get_instance()
    api.tool_manager.set_tool("placement")
    print(">> PlacementTool activated for generic device placement.")

# --- Device Wizard ---
@register_action("device.create_wizard")
def device_create_wizard(context):
    app = QApplication.instance()
    parent = app.activeWindow() if app else None
    wizard = DeviceWizard(parent)
    wizard.exec()

# --- Move Tool ---
@register_action("tool.move")
def tool_move(context):
    api = APIManager.get_instance()
    if not hasattr(api.tool_manager, '_tools') or 'move' not in api.tool_manager._tools:
        api.tool_manager.register_tool("move", MoveTool())
    api.tool_manager.set_tool("move")

# --- File Operations ---
@register_action("file.new")
def file_new(context):
    api = APIManager.get_instance()
    from infra.context import ProjectContext
    api.context = ProjectContext()
    api.context.undo_stack.clear()
    api.context.current_file = None
    api.context.dirty = False
    window = QApplication.activeWindow()
    if window and hasattr(window, 'canvas'):
        window.canvas.load_harness(api.context.harness)
    print(">> COMMAND: New File executed.")

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

@register_action("file.open")
def file_open(context):
    from infra.context import ProjectContext
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

# --- Edit Operations ---
@register_action("edit.undo")
def edit_undo(context):
    api = APIManager.get_instance()
    api.context.undo_stack.undo()

@register_action("edit.redo")
def edit_redo(context):
    api = APIManager.get_instance()
    api.context.undo_stack.redo()

@register_action("edit.delete")
def edit_delete(context):
    """Performs unified model deletion and UI refresh."""
    from core.selection import SelectionManager
    api = APIManager.get_instance()
    harness = api.context.harness
    mgr = SelectionManager()
    
    ids_to_remove = set(mgr.current_selection_ids)
    if not ids_to_remove:
        print(">> Delete: Nothing selected.")
        return

    # 1. Update Logic Models
    harness.devices = [d for d in harness.devices if d.id not in ids_to_remove]
    harness.wires = [
        w for w in harness.wires 
        if getattr(w, 'from_conn', None) not in ids_to_remove 
        and getattr(w, 'to_conn', None) not in ids_to_remove
    ]

    # 2. Reset selection state
    mgr.clear_selection()

    # 3. Synchronize UI
    window = QApplication.activeWindow()
    if window and hasattr(window, 'canvas'):
        window.canvas.load_harness(harness)
    
    print(f">> Deleted {len(ids_to_remove)} items and refreshed canvas.")

# --- Tools ---
@register_action("tool.select")
def tool_select(context):
    APIManager.get_instance().tool_manager.set_tool("select")

@register_action("tool.wire")
def tool_wire(context):
    APIManager.get_instance().tool_manager.set_tool("wire")

@register_action("file.export_bom")
def file_export_bom(context):
    from infra.bom import BOMGenerator
    path, _ = QFileDialog.getSaveFileName(None, "Export BOM", "bom.csv", "CSV Files (*.csv)")
    if path:
        gen = BOMGenerator(APIManager.get_instance().context)
        gen.generate_bom(path)