"""
Elbow command implementations for wire editing in Talus Trace.
Provides AddElbowCommand and DeleteElbowCommand for undo/redo of elbow operations.
"""
from infra.undo_stack import BaseCommand

class AddElbowCommand(BaseCommand):
    """
    Command to add an elbow (bend point) to a wire, supporting undo/redo.
    """
    def __init__(self, wire, insert_idx, pos):
        """
        Initialize AddElbowCommand.
        Args:
            wire: The wire to add the elbow to.
            insert_idx: Index to insert the elbow.
            pos: Position of the new elbow.
        """
        super().__init__("AddElbowCommand")
        self.wire = wire
        self.insert_idx = insert_idx
        self.pos = pos
        from api.manager import APIManager
        self.api = APIManager.get_instance()

    def _get_wire_item(self):
        """Look up the WireItem scene item for this wire via the API registry."""
        wire_id = getattr(self.wire, 'id', None)
        if wire_id is not None:
            return self.api.get_scene_item(wire_id)
        return None

    def execute(self):
        """
        Execute the command to add an elbow to the wire.
        """
        self.wire.path_nodes.insert(self.insert_idx, self.pos)
        wire_item = self._get_wire_item()
        if wire_item:
            wire_item._build_path_and_grips()
            wire_item.update()
        self.api.dispatch("model_changed", {"action": "add_elbow", "item": self.wire, "index": self.insert_idx})

    def undo(self):
        """
        Undo the command by removing the added elbow.
        """
        self.wire.path_nodes.pop(self.insert_idx)
        wire_item = self._get_wire_item()
        if wire_item:
            wire_item._build_path_and_grips()
            wire_item.update()
        self.api.dispatch("model_changed", {"action": "remove_elbow", "item": self.wire, "index": self.insert_idx})

class DeleteElbowCommand(BaseCommand):
    """
    Command to delete an elbow (bend point) from a wire, supporting undo/redo.
    """
    def __init__(self, wire, index):
        """
        Initialize DeleteElbowCommand.
        Args:
            wire: The wire to delete the elbow from.
            index: Index of the elbow to delete.
        """
        super().__init__("DeleteElbowCommand")
        self.wire = wire
        self.index = index
        self.old_pos = wire.path_nodes[index]
        from api.manager import APIManager
        self.api = APIManager.get_instance()

    def _get_wire_item(self):
        """Look up the WireItem scene item for this wire via the API registry."""
        wire_id = getattr(self.wire, 'id', None)
        if wire_id is not None:
            return self.api.get_scene_item(wire_id)
        return None

    def execute(self):
        """
        Execute the command to delete an elbow from the wire.
        """
        self.wire.path_nodes.pop(self.index)
        wire_item = self._get_wire_item()
        if wire_item:
            wire_item._build_path_and_grips()
            wire_item.update()
        self.api.dispatch("model_changed", {"action": "remove_elbow", "item": self.wire, "index": self.index})

    def undo(self):
        """
        Undo the command by restoring the deleted elbow.
        """
        self.wire.path_nodes.insert(self.index, self.old_pos)
        wire_item = self._get_wire_item()
        if wire_item:
            wire_item._build_path_and_grips()
            wire_item.update()
        self.api.dispatch("model_changed", {"action": "add_elbow", "item": self.wire, "index": self.index})
