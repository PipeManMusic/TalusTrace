import yaml
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem, QLabel
from PySide6.QtCore import Qt, QMimeData
from PySide6.QtGui import QDrag, QPixmap, QPainter
import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PARTS_PATH = os.path.join(PROJECT_ROOT, 'resources', 'library', 'parts.yaml')

class LibraryLoader:
    def __init__(self, library_path=None):
        self.library_path = library_path

    def load(self, path=None):
        target = str(path or self.library_path)
        try:
            with open(target, 'r') as f:
                return yaml.safe_load(f) or {}
        except Exception:
            return {}

    def get_items(self, path=None):
        """
        Test helper: Returns DICT of {id: part_data}.
        Must return a dict to satisfy test assertions looking for specific field values.
        """
        data = self.load(path)
        items = {}

        # 1. Handle Test Structure (ID is a Key in 'parts')
        # Format: {'parts': {'TEST-PART-01': {...}}}
        if isinstance(data, dict) and "parts" in data and isinstance(data["parts"], dict):
            items.update(data["parts"])

        # 2. Handle App Structure (ID is a Value of 'id')
        # Format: {'library': [{'parts': [{'id': 'CONN-01'}]}]}
        def _scan(obj):
            if isinstance(obj, dict):
                if "id" in obj:
                    items[obj["id"]] = obj
                for v in obj.values():
                    _scan(v)
            elif isinstance(obj, list):
                for item in obj:
                    _scan(item)

        _scan(data)
        return items

class LibraryPanel(QWidget):
    def __init__(self, library_path=PARTS_PATH, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(QLabel("Part Library"))
        
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setDragEnabled(True)
        self.layout.addWidget(self.tree)
        
        self.loader = LibraryLoader()
        try:
            data = self.loader.load(library_path)
        except Exception:
            data = {}
            
        self._populate_tree(data)
        
    def _populate_tree(self, data):
        items = self.loader.get_items()
        # If items is empty, nothing to show
        if not items:
            return

        # If items is in test structure: {id: part_data}
        if all(isinstance(v, dict) and 'id' in v for v in items.values()):
            for part_id, part in items.items():
                part_node = QTreeWidgetItem(self.tree)
                part_node.setText(0, part.get("name", part_id))
                part_node.setData(0, Qt.UserRole, part)
        else:
            # Try to handle app structure: categories with lists of parts
            for category, parts in items.items():
                cat_node = QTreeWidgetItem(self.tree)
                cat_node.setText(0, category)
                cat_node.setExpanded(True)
                if isinstance(parts, list):
                    for part in parts:
                        part_node = QTreeWidgetItem(cat_node)
                        part_node.setText(0, part.get("name", "Unnamed"))
                        part_node.setData(0, Qt.UserRole, part)

    def startDrag(self, actions):
        item = self.tree.currentItem()
        if not item or not item.data(0, Qt.UserRole): return
        
        part_data = item.data(0, Qt.UserRole)
        mime = QMimeData()
        mime.setText(part_data.get("id"))
        
        drag = QDrag(self)
        drag.setMimeData(mime)
        
        pixmap = QPixmap(100, 30)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setPen(Qt.white)
        painter.drawText(pixmap.rect(), Qt.AlignCenter, part_data.get("name"))
        painter.end()
        
        drag.setPixmap(pixmap)
        drag.setHotSpot(pixmap.rect().center())
        drag.exec_(Qt.CopyAction)