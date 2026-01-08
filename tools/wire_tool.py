from enum import Enum, auto

class WireToolState(Enum):
	IDLE = auto()
	DRAGGING = auto()

class WireTool:
	def __init__(self, harness):
		self.harness = harness
		self.state = WireToolState.IDLE
		self.start_pin = None

	def on_click(self, device_id=None, pin_id=None):
		if self.state == WireToolState.IDLE and pin_id:
			self.state = WireToolState.DRAGGING
			self.start_pin = pin_id
		elif self.state == WireToolState.DRAGGING and pin_id:
			# Create wire between start_pin and pin_id
			self.harness.wires.append(object())  # Dummy wire
			self.state = WireToolState.IDLE
			self.start_pin = None
		elif self.state == WireToolState.DRAGGING and not pin_id:
			# Ignore click on empty space
			pass
