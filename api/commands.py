import uuid
from core.device import Device
from core.pin import Pin, Side
# --- Place Generic Device ---
from api.actions import register_action
@register_action("tool.add_generic_device")
def tool_add_generic_device(context):
    # Enter placement mode instead of placing immediately
    from PySide6.QtWidgets import QApplication
    window = QApplication.activeWindow()
    if window and hasattr(window, 'canvas'):
        from tools.placement_tool import PlacementTool
        window.canvas.setFocus()
        window.canvas.set_active_tool(PlacementTool(window.canvas))
        window.canvas.active_tool.start()
        print(">> PlacementTool activated for generic device placement.")
from api.actions import register_action
from api.manager import APIManager
from PySide6.QtWidgets import QFileDialog, QApplication
from core.device import Device
from core.wire import Wire
from ui.dialogs.device_wizard import DeviceWizard
from tools.move_tool import MoveTool

# --- Device Wizard ---
@register_action("device.create_wizard")
def device_create_wizard(context):
    # Show the DeviceWizard dialog
    app = QApplication.instance()
    parent = app.activeWindow() if app else None
    wizard = DeviceWizard(parent)
    wizard.exec()

# --- Move Tool ---
@register_action("tool.move")
def tool_move(context):
    api = APIManager.get_instance()
    # Ensure MoveTool is registered
    if not hasattr(api.tool_manager, '_tools') or 'move' not in api.tool_manager._tools:
        api.tool_manager.register_tool("move", MoveTool())
    api.tool_manager.set_tool("move")

# --- File Operations ---
@register_action("file.new")
def file_new(context):
    """Clears harness.devices, harness.wires, and the undo stack. Refreshes the canvas."""
    api = APIManager.get_instance()
    from infra.context import ProjectContext
    api.context = ProjectContext()  # Reset context and harness
    api.context.undo_stack.clear()
    api.context.current_file = None
    api.context.dirty = False
    # Refresh the canvas if a window is open
    from PySide6.QtWidgets import QApplication
    window = QApplication.activeWindow()
    if window and hasattr(window, 'canvas'):
        window.canvas.load_harness(api.context.harness)
    print(">> COMMAND: New File executed. ProjectContext and harness reset. Canvas refreshed.")

@register_action("file.save_as")
def file_save_as(context):
    """Saves the current project context to a user-specified file and updates context.current_file."""
    api = APIManager.get_instance()
    ctx = api.context
    from PySide6.QtWidgets import QFileDialog
    path, _ = QFileDialog.getSaveFileName(None, "Save Harness File As", "harness.yaml", "YAML Files (*.yaml *.yml)")
    if not path:
        print(">> COMMAND: Save As cancelled.")
        return
    ctx.save_as(path)
    ctx.current_file = path
    print(f">> COMMAND: Save As executed. Saved to {path}")

@register_action("file.exit")
def file_exit(context):
    """Exits the application."""
    from PySide6.QtWidgets import QApplication
    print(">> COMMAND: Exiting application.")
    QApplication.quit()

@register_action("file.open")
def file_open(context):
    """Prompts for a YAML file and loads it into the project context."""
    from infra.context import ProjectContext
    api = APIManager.get_instance()
    path, _ = QFileDialog.getOpenFileName(None, "Open Harness File", "", "YAML Files (*.yaml *.yml)")
    if path:
        api.context = ProjectContext()
        api.context.load(path)
        api.context.current_file = path
        api.context.dirty = False
        print(f">> COMMAND: Open File executed. Loaded {path}")
    else:
        print(">> COMMAND: Open File cancelled.")

@register_action("file.save")
def file_save(context):
    """Saves the current project context to file, prompting if needed."""
    api = APIManager.get_instance()
    ctx = api.context
    path = getattr(ctx, 'current_file', None)
    if not path:
        path, _ = QFileDialog.getSaveFileName(None, "Save Harness File", "harness.yaml", "YAML Files (*.yaml *.yml)")
        if not path:
            print(">> COMMAND: Save File cancelled.")
            return
    ctx.save_as(path)
    print(f">> COMMAND: Save File executed. Saved to {path}")

# --- Edit Operations ---

@register_action("edit.undo")
def edit_undo(context):
    api = APIManager.get_instance()
    api.context.undo_stack.undo()
    # Canvas refresh is handled by MainWindow subscription
    print(">> COMMAND: Undo executed.")



@register_action("edit.undo")
def edit_undo(context):
    api = APIManager.get_instance()
    api.context.undo_stack.undo()
    print(">> COMMAND: Undo executed.")
    api.context.undo_stack.redo()

@register_action("edit.redo")
def edit_redo(context):
    api = APIManager.get_instance()
    api.context.undo_stack.redo()
    print(">> COMMAND: Redo executed.")
@register_action("edit.move")
def edit_move(context):
    print(">> COMMAND: Move Tool Activated.")

@register_action("edit.delete")
def edit_delete(context):
    # 1. Get Selection
    from core.selection import SelectionManager
    from ui.main_window import MainWindow
    api = APIManager.get_instance()
    harness = api.context.harness
    selection = SelectionManager().selected_models
    if not selection:
        print(">> Delete: Nothing selected.")
        return

    # Remove selected devices and connected wires by id (singleton enforced)
    ids_to_remove = set(SelectionManager().current_selection_ids)
    harness.devices = [d for d in harness.devices if d.id not in ids_to_remove]
    harness.wires = [w for w in harness.wires if getattr(w, 'from_conn', None) not in ids_to_remove and getattr(w, 'to_conn', None) not in ids_to_remove]
    SelectionManager().current_selection_ids.clear()
    # Refresh the canvas
    from PySide6.QtWidgets import QApplication
    window = QApplication.activeWindow()
    if window and hasattr(window, 'canvas'):
        window.canvas.load_harness(harness)
    print(f">> Deleted {len(ids_to_remove)} items and refreshed canvas.")

    # Clear selection
    SelectionManager().clear_selection()

    # Refresh the canvas
    from PySide6.QtWidgets import QApplication
    window = QApplication.activeWindow()
    if window and hasattr(window, 'canvas'):
        window.canvas.load_harness(harness)
    print(f">> Deleted {len(selection)} items and refreshed canvas.")

# --- Tools ---
@register_action("tool.select")
def tool_select(context):
    APIManager.get_instance().tool_manager.set_tool("select")

@register_action("tool.wire")
def tool_wire(context):
    APIManager.get_instance().tool_manager.set_tool("wire")

@register_action("tool.measure")
def tool_measure(context):
    print(">> COMMAND: Measure Tool Activated.")

# --- View Operations ---
@register_action("view.zoom_extents")
def view_zoom_extents(context):
    print(">> COMMAND: Zoom Extents executed.")

@register_action("view.toggle_props")
def view_toggle_props(context):
    print(">> COMMAND: Toggle Properties Panel.")

@register_action("file.export_bom")
def file_export_bom(context):
    from infra.bom import BOMGenerator
    
    # 1. Ask User for File
    mw = APIManager.get_instance().input_system.parent() # Hacky way to get window, or use active window
    path, _ = QFileDialog.getSaveFileName(None, "Export BOM", "bom.csv", "CSV Files (*.csv)")
    
    if path:
        gen = BOMGenerator(APIManager.get_instance().context)
        gen.generate_bom(path)