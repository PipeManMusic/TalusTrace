from PySide6.QtWidgets import QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem, QLabel
from PySide6.QtCore import Qt, QMimeData
from PySide6.QtGui import QDrag, QPixmap, QPainter
from api.manager import APIManager

class LibraryPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.api = APIManager.get_instance()
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0,0,0,0)
        self.layout.addWidget(QLabel("Parts Library"))
        
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setDragEnabled(True)
        self.layout.addWidget(self.tree)
        
        self.refresh()

    def refresh(self):
        self.tree.clear()
        parts = self.api.library.get_parts()
        
        # Simple Flat List for now, can group by manufacturer later
        for part_id, data in parts.items():
            item = QTreeWidgetItem(self.tree)
            name = data.get("description", part_id)
            item.setText(0, f"{part_id} - {name}")
            item.setData(0, Qt.UserRole, {**data, "id": part_id})

    def startDrag(self, actions):
        item = self.tree.currentItem()
        if not item: return
        
        data = item.data(0, Qt.UserRole)
        if not data: return
        
        mime = QMimeData()
        mime.setText(data.get("id"))
        # In a real impl, we'd set a specific mime type for drag-drop
        
        drag = QDrag(self)
        drag.setMimeData(mime)
        drag.exec_(Qt.CopyAction)
