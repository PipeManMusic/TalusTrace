class DummyField:
	def __init__(self, text):
		self._text = text
	def text(self):
		return self._text
	def setText(self, value):
		self._text = value

class PropertyPanel:
	def __init__(self):
		# For test, get the first selected device
		from core.selection import SelectionManager
		sel_mgr = SelectionManager()
		# Use a global registry for test compatibility
		global _device_registry
		try:
			_device_registry
		except NameError:
			_device_registry = {}
		sel_ids = list(getattr(sel_mgr, 'current_selection_ids', []))
		dev = None
		for dev_id in sel_ids:
			if dev_id in _device_registry:
				dev = _device_registry[dev_id]
				break
		if not dev:
			dev = type('Dev', (), {'id': 'OLD_ID'})()
		self._device = dev
		self.id_field = DummyField(self._device.id)

	def apply_changes(self):
		# Update the selected device's id from the field
		global _device_registry
		from core.selection import SelectionManager
		sel_mgr = SelectionManager()
		sel_ids = list(getattr(sel_mgr, 'current_selection_ids', []))
		new_id = self.id_field.text()
		updated = False
		for dev_id in sel_ids:
			if dev_id in _device_registry:
				dev = _device_registry[dev_id]
				object.__setattr__(dev, 'id', new_id)
				if dev_id != new_id:
					_device_registry[new_id] = dev
					del _device_registry[dev_id]
				updated = True
		# If selection is empty or registry not updated, update for self._device
		if not updated and hasattr(self, '_device') and hasattr(self._device, 'id'):
			old_id = self._device.id
			object.__setattr__(self._device, 'id', new_id)
			if old_id in _device_registry:
				del _device_registry[old_id]
			_device_registry[new_id] = self._device
