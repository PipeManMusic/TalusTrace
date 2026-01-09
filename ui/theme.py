

import yaml
from pathlib import Path
from PySide6.QtGui import QColor

class ThemeManager:
	def __init__(self, user_path=None):
		self.user_path = Path(user_path) if user_path else None
		self.colors = {"canvas_bg": "#2E2E2E"}
		if self.user_path and self.user_path.exists():
			self._load_user_theme()

	def _load_user_theme(self):
		from resources.defaults import DEFAULT_THEME
		try:
			with open(self.user_path, 'r') as f:
				data = yaml.safe_load(f)
				if "colors" in data:
					self.colors.update(data["colors"])
		except Exception:
			self.colors = DEFAULT_THEME.copy()

	def get_color(self, key):
		return self.colors.get(key, "#2E2E2E")

	def set_color_override(self, key, value):
		self.colors[key] = value

	def save_user_theme(self):
		if not self.user_path:
			raise ValueError("No user_path specified for ThemeManager")
		with open(self.user_path, 'w') as f:
			yaml.safe_dump({"colors": self.colors}, f)
