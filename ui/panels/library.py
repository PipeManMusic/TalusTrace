import yaml

class LibraryLoader:
	def __init__(self, library_path):
		self.library_path = library_path
		self._items = None

	def get_items(self):
		if self._items is not None:
			return self._items
		with open(self.library_path, 'r') as f:
			data = yaml.safe_load(f)
		self._items = data.get('parts', {})
		return self._items
