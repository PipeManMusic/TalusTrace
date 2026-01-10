from PySide6.QtWidgets import QApplication
from api.actions import register_action
from api.manager import APIManager

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
    from core.selection import SelectionManager
    api = APIManager.get_instance()
    harness = api.context.harness
    mgr = SelectionManager()
    
    ids_to_remove = set(mgr.current_selection_ids)
    if not ids_to_remove:
        print(">> Delete: Nothing selected.")
        return

    # Update Logic Models
    harness.devices = [d for d in harness.devices if d.id not in ids_to_remove]
    harness.wires = [
        w for w in harness.wires 
        if getattr(w, 'from_conn', None) not in ids_to_remove 
        and getattr(w, 'to_conn', None) not in ids_to_remove
    ]

    # Reset selection state
    mgr.clear_selection()

    # Synchronize UI
    window = QApplication.activeWindow()
    if window and hasattr(window, 'canvas'):
        window.canvas.load_harness(harness)
    
    print(f">> Deleted {len(ids_to_remove)} items and refreshed canvas.")

@register_action("edit.rotate_cw")
def edit_rotate_cw(context):
    """Rotates selected devices 90 degrees clockwise."""
    from core.selection import SelectionManager
    api = APIManager.get_instance()
    mgr = SelectionManager()
    
    if not mgr.selected_models:
        print(">> Rotate: Nothing selected.")
        return

    count = 0
    for item in mgr.selected_models:
        if hasattr(item, 'rotation'):
            current = getattr(item, 'rotation', 0) or 0
            item.rotation = (current + 90) % 360
            count += 1
    
    if count > 0:
        window = QApplication.activeWindow()
        if window and hasattr(window, 'canvas'):
            window.canvas.load_harness(api.context.harness)
        print(f">> Rotated {count} items.")
