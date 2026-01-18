from infra.undo_stack import BaseCommand

class AddElbowCommand(BaseCommand):
    def __init__(self, wire, insert_idx, pos):
        super().__init__("AddElbowCommand")
        self.wire = wire
        self.insert_idx = insert_idx
        self.pos = pos
        from api.manager import APIManager
        self.api = APIManager.get_instance()

    def execute(self):
        self.wire.path_nodes.insert(self.insert_idx, self.pos)
        if hasattr(self.wire, 'ui_item') and self.wire.ui_item:
            self.wire.ui_item._build_path_and_grips()
            self.wire.ui_item.update()
            # Ensure grips are visible by reselecting the wire
            if hasattr(self.wire, 'id'):
                self.api.select([self.wire.id])
        self.api.dispatch("model_changed", {"action": "add_elbow", "item": self.wire, "index": self.insert_idx})

    def undo(self):
        self.wire.path_nodes.pop(self.insert_idx)
        if hasattr(self.wire, 'ui_item') and self.wire.ui_item:
            self.wire.ui_item._build_path_and_grips()
            self.wire.ui_item.update()
        self.api.dispatch("model_changed", {"action": "remove_elbow", "item": self.wire, "index": self.insert_idx})

class DeleteElbowCommand(BaseCommand):
    def __init__(self, wire, index):
        super().__init__("DeleteElbowCommand")
        self.wire = wire
        self.index = index
        self.old_pos = wire.path_nodes[index]
        from api.manager import APIManager
        self.api = APIManager.get_instance()

    def execute(self):
        self.wire.path_nodes.pop(self.index)
        if hasattr(self.wire, 'ui_item') and self.wire.ui_item:
            self.wire.ui_item.setSelected(True)  # Ensure grips are rebuilt and visible
            self.wire.ui_item._build_path_and_grips()
            self.wire.ui_item.update()
            # Ensure grips are visible by reselecting the wire
            if hasattr(self.wire, 'id'):
                self.api.select([self.wire.id])
        self.api.dispatch("model_changed", {"action": "remove_elbow", "item": self.wire, "index": self.index})

    def undo(self):
        self.wire.path_nodes.insert(self.index, self.old_pos)
        if hasattr(self.wire, 'ui_item') and self.wire.ui_item:
            self.wire.ui_item.setSelected(True)  # Ensure grips are rebuilt and visible
            self.wire.ui_item._build_path_and_grips()
            self.wire.ui_item.update()
        self.api.dispatch("model_changed", {"action": "add_elbow", "item": self.wire, "index": self.index})
