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
from PySide6.QtCore import Qt, QMimeData
from PySide6.QtGui import QDrag
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
        self.tree = _LibraryTree(self)
        self.tree.setHeaderLabel(I18N.get('library_panel_header'))
        self.tree.header().setVisible(False)
        self.tree.setDragEnabled(True) # Allow dragging parts
        self.tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._on_context_menu)
        layout.addWidget(self.tree)

        # Auto-refresh whenever the library changes (e.g. a part is added,
        # edited, or deleted via the wizard), so the tree stays in sync
        # without requiring a restart.
        if hasattr(self.api, "subscribe"):
            self.api.subscribe("library_changed", self.refresh)

        self.refresh()

    def refresh(self, *args, **kwargs):
        """
        Refresh the parts tree from the API's library data.
        Groups parts by category and populates the tree view.
        """
        self.tree.clear()
        # PHASE 5 FIX: Ask API for data, don't read files here.
        if hasattr(self.api, 'library'):
            parts = self.api.library.get_parts()
            # Normalize to list[(part_id, part_def)] so each entry carries its id.
            if isinstance(parts, dict):
                parts_iter = list(parts.items())
            elif isinstance(parts, list):
                parts_iter = [(p.get('id', ''), p) for p in parts if isinstance(p, dict)]
            else:
                parts_iter = []
            # Group by Category (e.g. connectors, splices)
            categories = {}
            for part_id, part in parts_iter:
                if not isinstance(part, dict):
                    continue
                cat = part.get('category') or 'Uncategorized'
                if cat not in categories:
                    categories[cat] = QTreeWidgetItem(self.tree, [str(cat).title()])
                    categories[cat].setExpanded(True)
                name = part.get('name') or part_id or 'Unknown'
                item = QTreeWidgetItem(categories[cat], [name])
                # Store Part ID in UserRole for drag/drop and double-click.
                item.setData(0, Qt.UserRole, part_id)
        else:
            # Fallback if library didn't load
            QTreeWidgetItem(self.tree, ["Library Offline"])

    # -- user actions ------------------------------------------------------
    def _on_item_double_clicked(self, item, _column):
        """Instantiate the clicked library part into the current harness."""
        part_id = item.data(0, Qt.UserRole)
        if not part_id:
            return  # category row or malformed entry
        try:
            self.api.create_device_from_part(part_id)
        except Exception:
            from infra.logging import infra_log
            infra_log(f"[LibraryPanel] Failed to instantiate part '{part_id}'", level="error")

    def _on_context_menu(self, pos):
        """Show a right-click menu offering to edit the clicked library part."""
        item = self.tree.itemAt(pos)
        if item is None:
            return
        part_id = item.data(0, Qt.UserRole)
        if not part_id:
            return  # category row, not an editable part
        from PySide6.QtWidgets import QMenu
        from ui.i18n import I18N
        menu = QMenu(self.tree)
        edit_action = menu.addAction(I18N.get("library_edit_part", "Edit Part…"))
        delete_action = menu.addAction(I18N.get("library_delete_part", "Delete Part…"))
        chosen = menu.exec(self.tree.viewport().mapToGlobal(pos))
        if chosen is edit_action:
            self.edit_part(part_id)
        elif chosen is delete_action:
            self.delete_part(part_id, item.text(0))

    def edit_part(self, part_id):
        """Open the device wizard pre-filled with an existing library part."""
        from ui.dialogs.device_wizard import DeviceWizard
        wizard = DeviceWizard(self, edit_part_id=part_id)
        if wizard.exec():
            self.refresh()

    def delete_part(self, part_id, part_name=None):
        """Prompt for confirmation, then delete a library part via the API."""
        from PySide6.QtWidgets import QMessageBox
        from ui.i18n import I18N
        label = part_name or part_id
        confirm = QMessageBox.question(
            self,
            I18N.get("library_delete_part_title", "Delete Part"),
            I18N.get(
                "library_delete_part_confirm",
                "Delete '{name}' from the library? This cannot be undone.",
            ).format(name=label),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if confirm != QMessageBox.Yes:
            return
        if self.api.delete_library_part(part_id):
            self.refresh()



class _LibraryTree(QTreeWidget):
    """QTreeWidget that emits ``library://<part_id>`` mime on drag start.

    The existing :meth:`APIManager.handle_drop` already understands this scheme,
    so dragging a leaf onto the canvas places the device at the drop position.
    """

    def startDrag(self, supported_actions):  # noqa: N802 (Qt name)
        """Attach ``library://<part_id>`` mime text so canvas drop handler can consume it."""
        item = self.currentItem()
        if item is None:
            return
        part_id = item.data(0, Qt.UserRole)
        if not part_id:
            return
        mime = QMimeData()
        mime.setText(f"library://{part_id}")
        drag = QDrag(self)
        drag.setMimeData(mime)

        # Attach a small drag pixmap so the cursor clearly shows a part is
        # being dragged (otherwise the cursor gives no drag feedback).
        pixmap = self._make_drag_pixmap(item.text(0) or part_id)
        if pixmap is not None:
            drag.setPixmap(pixmap)
            drag.setHotSpot(pixmap.rect().center())

        # Force a Copy action so the cursor shows the "+" copy affordance.
        drag.exec(supported_actions, Qt.CopyAction)

    @staticmethod
    def _make_drag_pixmap(label):
        """Render a small labelled chip to use as the drag cursor pixmap."""
        from PySide6.QtGui import QPixmap, QPainter, QColor, QFont
        from PySide6.QtCore import QRectF
        text = str(label)
        font = QFont()
        font.setPointSize(9)
        metrics = None
        try:
            from PySide6.QtGui import QFontMetrics
            metrics = QFontMetrics(font)
        except Exception:
            pass
        width = (metrics.horizontalAdvance(text) + 16) if metrics else (len(text) * 8 + 16)
        height = 22
        pixmap = QPixmap(width, height)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setBrush(QColor(40, 40, 40, 220))
        painter.setPen(QColor(120, 170, 255))
        painter.drawRoundedRect(QRectF(0.5, 0.5, width - 1, height - 1), 4, 4)
        painter.setPen(QColor(230, 230, 230))
        painter.setFont(font)
        painter.drawText(pixmap.rect(), Qt.AlignCenter, text)
        painter.end()
        return pixmap
