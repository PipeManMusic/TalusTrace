
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
		self.elbow_drag = False
		if hasattr(event, 'scene_item'):
			item = event.scene_item
			# BundleItem elbow detection
			if hasattr(item, 'path_nodes'):
				pos = event.pos_mm
				min_dist = 5.0  # mm radius for elbow selection (per spec)
				for idx, node in enumerate(item.path_nodes):
					dist = ((pos.x() - node[0]) ** 2 + (pos.y() - node[1]) ** 2) ** 0.5
					if dist < min_dist:
						self.elbow_index = idx
						self.selected_item = item
						self.elbow_drag = True
						break
			# DeviceItem fallback
			elif hasattr(item, 'device'):
				self._target = item.device
				self.ghost_item = type(self._target)(**self._target.model_dump())
				self.selected_item = item

	def on_mouse_release(self, event):
		# Commit elbow drag for BundleItem
		if getattr(self, 'elbow_drag', False) and self.selected_item is not None and hasattr(self.selected_item, 'path_nodes'):
			# Commit the new path to the Wire model (if available)
			# Ensure wire_diameters are present
			if not hasattr(self.selected_item, 'wire_diameters') or not self.selected_item.wire_diameters:
				self.selected_item.wire_diameters = [1.0 for _ in self.selected_item.path_nodes]
			# If the BundleItem has a wire model, update its path
			if hasattr(self.selected_item, 'device') and self.selected_item.device:
				self.selected_item.device.path_nodes = list(self.selected_item.path_nodes)
			self.elbow_drag = False
			self.elbow_index = None
			self.selected_item = None
			return
		# Only push if a ghost move was performed (DeviceItem)
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
		if self.selected_item is not None:
			cur_pos = self.selected_item.pos()
			new_pos = cur_pos + type(cur_pos)(dx, dy)
			self.selected_item.setPos(new_pos)
			self.selected_item.update()
			device = getattr(self.selected_item, 'device', None)
			if device is not None:
				device.x = new_pos.x()
				device.y = new_pos.y()
			# Update all BundleItems connected to this device by id
			if hasattr(self.selected_item, 'scene') and self.selected_item.scene() is not None:
				scene = self.selected_item.scene()
				for item in scene.items():
					if hasattr(item, 'device') and item.device is not None:
						wire = item.device
						if hasattr(wire, 'from_conn') and hasattr(wire, 'to_conn'):
							if wire.from_conn == device.id or wire.to_conn == device.id:
								# Recalculate path_nodes using updated device and pin positions
								def find_device(dev_id):
									for dev_item in scene.items():
										if hasattr(dev_item, 'device') and hasattr(dev_item.device, 'id'):
											if dev_item.device.id == dev_id:
												return dev_item.device
									return None
								d_from = find_device(wire.from_conn)
								d_to = find_device(wire.to_conn)
								def find_pin(device, pin_id):
									if device and hasattr(device, 'pins'):
										for pin in device.pins:
											if pin.id == pin_id:
												return pin
									return None
								pin_from = find_pin(d_from, getattr(wire, 'from_pin', ''))
								pin_to = find_pin(d_to, getattr(wire, 'to_pin', ''))
								from_pt = (d_from.x + (pin_from.x if pin_from else 0), d_from.y + (pin_from.y if pin_from else 0)) if d_from else (0, 0)
								to_pt = (d_to.x + (pin_to.x if pin_to else 0), d_to.y + (pin_to.y if pin_to else 0)) if d_to else (0, 0)
								new_nodes = [from_pt] + list(getattr(wire, 'points', [])) + [to_pt]
								item.path_nodes = new_nodes
								if not hasattr(item, 'wire_diameters') or len(item.wire_diameters) != len(new_nodes):
									item.wire_diameters = [1.0] * len(new_nodes)
								from PySide6.QtGui import QPainterPath
								qpath = QPainterPath()
								if new_nodes:
									qpath.moveTo(new_nodes[0][0], new_nodes[0][1])
									for node in new_nodes[1:]:
										qpath.lineTo(node[0], node[1])
									item.setPath(qpath)
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
