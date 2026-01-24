
"""
Action for deleting selected items in Talus Trace.
Implements the 'edit.delete' action and handles selection/model removal.
"""
from api.actions import register_action

@register_action("edit.delete")
def delete_selected(context):
    """
    Deletes the currently selected items from the model.
    Args:
        context: The action context containing application state.
    """
    from api.manager import APIManager
    from core.selection import SelectionManager
    print("[DEBUG] edit.delete action called")
    api = APIManager.get_instance()
    selection = SelectionManager().selected_models[:]
    print(f"[DEBUG] Selection for delete: {[getattr(m, 'id', None) for m in selection]}")
    from core.selection import SelectionManager
    for model in selection:
        # Remove from model
        if hasattr(api.context.harness, 'devices') and model in api.context.harness.devices:
            print(f"[DEBUG] Removing device {getattr(model, 'id', None)} from model")
            api.context.harness.devices.remove(model)
            # If the deleted device was selected, clear selection
            if model in SelectionManager().selected_models:
                SelectionManager().clear_selection()
                api.dispatch("selection_changed", {"selection": []})
            # Dispatch model_changed for UI update
            print(f"[DEBUG] Dispatching model_changed remove for {getattr(model, 'id', None)}")
            api.dispatch("model_changed", {"action": "remove", "item": model})
        # TODO: handle wires, other types as needed
