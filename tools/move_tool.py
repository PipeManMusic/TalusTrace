
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
	def activate(self):
		pass

	def deactivate(self):
		pass

	def on_mouse_press(self, event):
		# Elbow drag for BundleItem
		self.elbow_index = None
		if hasattr(event, 'scene_item'):
			item = event.scene_item
			# BundleItem elbow detection
			if hasattr(item, 'path_nodes'):
				pos = event.pos_mm
				min_dist = 10.0  # mm radius for elbow selection
				for idx, node in enumerate(item.path_nodes):
					dist = ((pos.x() - node[0]) ** 2 + (pos.y() - node[1]) ** 2) ** 0.5
					if dist < min_dist:
						self.elbow_index = idx
						self.selected_item = item
						break
			# DeviceItem fallback
			elif hasattr(item, 'device'):
				self._target = item.device
				self.ghost_item = type(self._target)(**self._target.model_dump())
				self.selected_item = item

	def on_mouse_release(self, event):
		# Only push if a ghost move was performed
		if self.ghost_item is None:
			return
		api = APIManager.get_instance()
		cmd = self.commit()
		api.context.undo_stack.push(cmd)

	def on_mouse_move(self, event):
		# Elbow drag for BundleItem
		if hasattr(event, 'pos_mm') and hasattr(event, 'scene_item'):
			item = event.scene_item
			grid_size = 25.0
			import math
			def snap(val):
				return math.floor(val / grid_size) * grid_size
			if hasattr(item, 'path_nodes') and self.elbow_index is not None:
				# Snap elbow to grid
				x = snap(event.pos_mm.x())
				y = snap(event.pos_mm.y())
				item.path_nodes[self.elbow_index] = (x, y)
				# Optionally update visual path if needed
				if hasattr(item, 'setPath'):
					from PySide6.QtGui import QPainterPath
					qpath = QPainterPath()
					nodes = item.path_nodes
					if nodes:
						qpath.moveTo(nodes[0][0], nodes[0][1])
						for node in nodes[1:]:
							qpath.lineTo(node[0], node[1])
					item.setPath(qpath)
			elif hasattr(item, 'device'):
				dev = item.device
				dev.x = snap(event.pos_mm.x())
				dev.y = snap(event.pos_mm.y())
	def __init__(self):
		self.ghost_item = None
		self._target = None
		self.selected_item = None  # QGraphicsItem for the device

	def start(self, target, selected_item=None):
		# Create a ghost copy (shallow for test)
		self._target = target
		self.ghost_item = type(target)(**target.model_dump())
		self.selected_item = selected_item

	def update(self, dx, dy):
		if self.ghost_item:
			self.ghost_item.x += dx
			self.ghost_item.y += dy
		# For UI: only move the visual, not the model, during drag
		if self.selected_item is not None:
			# Get current pos and add delta
			cur_pos = self.selected_item.pos()
			new_pos = cur_pos + type(cur_pos)(dx, dy)
			self.selected_item.setPos(new_pos)
			self.selected_item.update()
			# Redraw wires connected to this device
			if hasattr(self.selected_item, 'scene') and self.selected_item.scene() is not None:
				for item in self.selected_item.scene().items():
					if hasattr(item, 'device') and hasattr(self.selected_item, 'device') and item.device == self.selected_item.device:
						if hasattr(item, 'update_compliance_visuals'):
							item.update_compliance_visuals()
						item.update()

	def commit(self):
		# On commit, update the model to match the visual
		if self.selected_item is not None and hasattr(self.selected_item, 'device'):
			pos = self.selected_item.pos()
			self.selected_item.device.x = pos.x()
			self.selected_item.device.y = pos.y()
		# Return a MoveCommand for the move
		return MoveCommand(self._target, self.ghost_item.x, self.ghost_item.y)

	def on_mouse_release(self, event):
		# Only push if a ghost move was performed
		if self.ghost_item is None:
			return
		api = APIManager.get_instance()
		cmd = self.commit()
		api.context.undo_stack.push(cmd)
