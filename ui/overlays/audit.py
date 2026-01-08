class DummyMarker:
	def __init__(self, message):
		self._message = message
	def toolTip(self):
		return self._message

class AuditOverlay:
	def __init__(self):
		self.markers = []
	def update_markers(self, violations):
		def extract_message(v):
			if isinstance(v, dict) and 'message' in v:
				return v['message']
			return getattr(v, 'message', str(v))
		self.markers = [DummyMarker(extract_message(v)) for v in violations]
