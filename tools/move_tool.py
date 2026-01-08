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
		# Return a command that applies the ghost's position to the real object
		class MoveCommand:
			def __init__(self, x, y):
				self.x = x
				self.y = y
			def apply(self, target):
				target.x = self.x
				target.y = self.y
			def execute(self, target):
				self.apply(target)
		return MoveCommand(self.ghost_item.x, self.ghost_item.y)
