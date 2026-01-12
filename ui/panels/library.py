from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget, QHeaderView
from PySide6.QtCore import Qt
from api.manager import APIManager

class LibraryPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.api = APIManager.get_instance()
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        
        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("Component Library")
        self.tree.header().setVisible(False)
        self.tree.setDragEnabled(True) # Allow dragging parts
        layout.addWidget(self.tree)
        
        self.refresh()

    def refresh(self):
        self.tree.clear()
        
        # PHASE 5 FIX: Ask API for data, don't read files here.
        if hasattr(self.api, 'library'):
            parts = self.api.library.get_parts()
            
            # Group by Category (e.g. connectors, splices)
            categories = {}
            
            for part_id, part_data in parts.items():
                cat = part_data.get('category', 'Uncategorized')
                if cat not in categories:
                    categories[cat] = QTreeWidgetItem(self.tree, [cat.title()])
                    categories[cat].setExpanded(True)
                
                name = part_data.get('name', part_id)
                item = QTreeWidgetItem(categories[cat], [name])
                # Store Part ID in UserRole
                item.setData(0, Qt.UserRole, part_id)
        else:
            # Fallback if library didn't load
            err = QTreeWidgetItem(self.tree, ["Library Offline"])