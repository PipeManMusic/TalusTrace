from api.actions import register_action
from api.manager import APIManager
from PySide6.QtWidgets import QFileDialog

# --- File Operations ---
@register_action("file.new")
def file_new(context):
    """Resets the project to a new harness and clears undo stack."""
    from infra.context import ProjectContext
    api = APIManager.get_instance()
    api.context = ProjectContext()  # New context with new Harness
    api.context.undo_stack.clear()
    api.context.current_file = None
    api.context.dirty = False
    print(">> COMMAND: New File executed. Project reset.")

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
    print(">> COMMAND: Undo executed.")

@register_action("edit.redo")
def edit_redo(context):
    print(">> COMMAND: Redo executed.")

@register_action("edit.move")
def edit_move(context):
    print(">> COMMAND: Move Tool Activated.")

@register_action("edit.delete")
def edit_delete(context):
    # 1. Get Selection
    from core.selection import SelectionManager
    selection = SelectionManager().selected_models
    if not selection:
        print(">> Delete: Nothing selected.")
        return

    api = APIManager.get_instance()
    harness = api.context.harness
    scene = None
    
    # Try to get scene from Active Window
    window = QApplication.activeWindow()
    if window and hasattr(window, 'canvas'):
        scene = window.canvas.scene

    count = 0
    for model in list(selection): # Copy list to safely modify original
        # A. Remove from Model
        if isinstance(model, Device):
            if model in harness.devices:
                harness.devices.remove(model)
                count += 1
        elif isinstance(model, Wire):
            if model in harness.wires:
                harness.wires.remove(model)
                count += 1
        
        # B. Remove from Scene (Visuals)
        if scene:
            # Find item linked to this model
            # (Naive search; ideal is a map, but this works for Phase 5)
            for item in scene.items():
                if hasattr(item, 'device') and item.device == model:
                    scene.removeItem(item)
                    break
    
    # Clear Selection
    SelectionManager().set_selection([])
    print(f">> Deleted {count} items.")

# --- Tools ---
@register_action("tool.select_mode")
def tool_select(context):
    APIManager.get_instance().tool_manager.set_tool("select")

@register_action("tool.wire_mode")
def tool_wire(context):
    # This was likely missing or commented out
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