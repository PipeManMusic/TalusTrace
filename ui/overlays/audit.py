"""
Audit overlay classes for Talus Trace UI.

Provides overlay marker and audit visualization support.
"""

class DummyMarker:
	"""A simple marker class for audit overlays, holding a tooltip message."""
	def __init__(self, message):
		"""Initialize DummyMarker with a message."""
		self._message = message
	def toolTip(self):
		"""Return the tooltip message for the marker."""
		return self._message

class AuditOverlay:
	"""Overlay for displaying audit markers in the UI."""
	def __init__(self):
		"""Initialize AuditOverlay with an empty marker list."""
		self.markers = []
	def update_markers(self, violations):
		"""Update the overlay markers based on a list of violations."""
		def extract_message(v):
			"""Extract a message string from a violation object or dictionary."""
			if isinstance(v, dict) and 'message' in v:
				return v['message']
			return getattr(v, 'message', str(v))
		self.markers = [DummyMarker(extract_message(v)) for v in violations]
