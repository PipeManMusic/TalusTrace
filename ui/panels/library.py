import yaml
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem, QLabel
from PySide6.QtCore import Qt, QMimeData
from PySide6.QtGui import QDrag, QPixmap, QPainter, QColor

class LibraryPanel(QWidget):
    def __init__(self, library_path="resources/library/parts.yaml", parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        
        # Header
        self.layout.addWidget(QLabel("Part Library"))
        
        # Tree
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setDragEnabled(True) # Enable Dragging
        self.layout.addWidget(self.tree)
        
        # Load Data
        self._load_library(library_path)
        
    def _load_library(self, path):
        try:
            with open(path, 'r') as f:
                data = yaml.safe_load(f) or {}
                
            categories = data.get("library", [])
            for cat in categories:
                # Create Category Node
                cat_node = QTreeWidgetItem(self.tree)
                cat_node.setText(0, cat.get("category", "Unknown"))
                cat_node.setExpanded(True)
                
                # Create Part Nodes
                for part in cat.get("parts", []):
                    part_node = QTreeWidgetItem(cat_node)
                    part_node.setText(0, part.get("name", "Unnamed"))
                    # Store metadata for the drag event
                    part_node.setData(0, Qt.UserRole, part)
                    
        except Exception as e:
            print(f"Library Load Error: {e}")

    # --- Drag Logic ---
    def startDrag(self, actions):
        """
        Called when user drags a tree item.
        """
        item = self.tree.currentItem()
        if not item or not item.data(0, Qt.UserRole):
            return # Don't drag categories
            
        part_data = item.data(0, Qt.UserRole)
        
        # 1. Create Mime Data (The Payload)
        mime = QMimeData()
        mime.setText(part_data.get("id")) # Simple ID transfer for now
        # We could dump the whole JSON here if needed
        
        # 2. Create the Visual Drag Object
        drag = QDrag(self)
        drag.setMimeData(mime)
        
        # 3. Create a Ghost Pixmap
        pixmap = QPixmap(100, 30)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setPen(Qt.white)
        painter.drawText(pixmap.rect(), Qt.AlignCenter, part_data.get("name"))
        painter.end()
        
        drag.setPixmap(pixmap)
        drag.setHotSpot(pixmap.rect().center())
        
        drag.exec_(Qt.CopyAction)