from PySide6.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QLabel, QLineEdit, QScrollArea
from PySide6.QtCore import Qt
from api.manager import APIManager
from core.device import Device
from core.wire import Wire

class PropertyPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Properties")
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0,0,0,0)
        
        # Header
        self.header = QLabel("Properties")
        self.header.setStyleSheet("font-weight: bold; padding: 5px;")
        self.layout.addWidget(self.header)
        
        # Scroll Area for Content
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.content_widget = QWidget()
        self.form_layout = QFormLayout(self.content_widget)
        self.scroll.setWidget(self.content_widget)
        self.layout.addWidget(self.scroll)
        
        # Initial State
        self.clear_panel()
        
        # Register Listener
        # UPDATE: Changed .observe() to .subscribe()
        APIManager.get_instance().subscribe(self._on_app_event)

    def _on_app_event(self, event_data):
        try:
            # SAFETY CHECK: If C++ object is deleted, this access will raise RuntimeError
            if not self.isVisible() and False: pass 
            
            action = event_data.get("event")
            
            if action == "selection_changed":
                selection = event_data.get("selection", [])
                if selection:
                    self.load_item(selection[0])
                else:
                    self.clear_panel()
                    
        except RuntimeError:
            pass

    def clear_panel(self):
        self._clear_layout()
        self.form_layout.addRow(QLabel("No Selection"))

    def _clear_layout(self):
        while self.form_layout.count():
            item = self.form_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()

    def load_item(self, item):
        self._clear_layout()
        
        if isinstance(item, Device):
            self.header.setText(f"Device: {item.id}")
            self._add_field("ID", item.id, item, "id")
            self._add_field("Label", item.label, item, "label")
            self._add_field("X (mm)", str(item.x), item, "x")
            self._add_field("Y (mm)", str(item.y), item, "y")
            
        elif isinstance(item, Wire):
            self.header.setText(f"Wire: {item.id}")
            self._add_field("ID", item.id, item, "id")
            self._add_field("From", item.from_conn, item, "from_conn")
            self._add_field("To", item.to_conn, item, "to_conn")
            self._add_field("Color", item.color, item, "color")

    def _add_field(self, label, value, obj, attr_name):
        edit = QLineEdit(str(value))
        edit.editingFinished.connect(lambda: self._update_model(obj, attr_name, edit.text()))
        self.form_layout.addRow(label, edit)
        if attr_name == "id": self.id_edit = edit
        if attr_name == "label": self.label_edit = edit

    def _update_model(self, obj, attr, value):
        if hasattr(obj, attr):
            current_type = type(getattr(obj, attr))
            try:
                if current_type == float:
                    val = float(value)
                elif current_type == int:
                    val = int(value)
                else:
                    val = value
                setattr(obj, attr, val)
                print(f">> Updated {attr} -> {val}")
            except ValueError:
                print(f"Invalid input for {attr}")