
from infra.undo_stack import BaseCommand
from api.manager import APIManager

class MoveCommand(BaseCommand):
	def __init__(self, target, new_x, new_y):
		super().__init__("MoveCommand")
		self.target = target
		self.new_x = new_x
		self.new_y = new_y
		self.old_x = target.x
		self.old_y = target.y

	def execute(self, target=None):
		tgt = target if target is not None else self.target
		tgt.x = self.new_x
		tgt.y = self.new_y

	def undo(self):
		self.target.x = self.old_x
		self.target.y = self.old_y

class MoveTool:
	def __init__(self):
		self.ghost_item = None
		self._target = None

	def start(self, target):
		# Create a ghost copy (shallow for test)
		self._target = target
		self.ghost_item = type(target)(**target.model_dump())

	def update(self, dx, dy):
		if self.ghost_item:
			self.ghost_item.x += dx
			self.ghost_item.y += dy

	def commit(self):
		# Return a MoveCommand for the move
		return MoveCommand(self._target, self.ghost_item.x, self.ghost_item.y)

	def on_mouse_release(self, event):
		# Only push if a ghost move was performed
		if self.ghost_item is None:
			return
		api = APIManager.get_instance()
		cmd = self.commit()
		api.context.undo_stack.push(cmd)
