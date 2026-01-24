"""
LibraryPanel and LibraryLoader: UI and data loader for the parts library panel.
Provides a tree view of available parts grouped by category.
"""
# Minimal LibraryLoader for test compatibility
class LibraryLoader:
    """
    Loads parts library data from a YAML file for test compatibility.
    """
    def __init__(self, library_path=None):
        """
        Initialize the LibraryLoader.
        Args:
            library_path (str): Path to the library YAML file.
        """
        self.library_path = library_path

    def get_items(self):
        """
        Load and return parts from the YAML library file.
        Returns:
            dict: Dictionary of parts from the library file.
        """
        import yaml
        if not self.library_path:
            return {}
        with open(self.library_path, 'r') as f:
            data = yaml.safe_load(f) or {}
        return data.get("parts", {})
from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget, QHeaderView
from PySide6.QtCore import Qt
from api.manager import APIManager

class LibraryPanel(QWidget):
    """
    QWidget panel that displays the parts library in a tree view grouped by category.
    """
    def __init__(self, parent=None):
        """
        Initialize the LibraryPanel UI and load the parts tree.
        Args:
            parent: Optional parent QWidget.
        """
        super().__init__(parent)
        self.api = APIManager.get_instance()
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        
        from ui.i18n import I18N
        self.tree = QTreeWidget()
        self.tree.setHeaderLabel(I18N.get('library_panel_header'))
        self.tree.header().setVisible(False)
        self.tree.setDragEnabled(True) # Allow dragging parts
        layout.addWidget(self.tree)
        
        self.refresh()

    def refresh(self):
        """
        Refresh the parts tree from the API's library data.
        Groups parts by category and populates the tree view.
        """
        self.tree.clear()
        # PHASE 5 FIX: Ask API for data, don't read files here.
        if hasattr(self.api, 'library'):
            parts = self.api.library.get_parts()
            # If parts is a dict, iterate over its values
            if isinstance(parts, dict):
                parts_iter = parts.values()
            elif isinstance(parts, list):
                parts_iter = parts
            else:
                parts_iter = []
            # Group by Category (e.g. connectors, splices)
            categories = {}
            for part in parts_iter:
                cat = part.get('category', 'Uncategorized')
                if cat not in categories:
                    categories[cat] = QTreeWidgetItem(self.tree, [cat.title()])
                    categories[cat].setExpanded(True)
                name = part.get('name', part.get('id', 'Unknown'))
                item = QTreeWidgetItem(categories[cat], [name])
                # Store Part ID in UserRole
                item.setData(0, Qt.UserRole, part.get('id', ''))
        else:
            # Fallback if library didn't load
            err = QTreeWidgetItem(self.tree, ["Library Offline"])