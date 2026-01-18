from PySide6.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QLabel, QLineEdit, QScrollArea
from core.device import Device, Pin
from core.wire import Wire
from api.manager import APIManager
from api.commands.edit import UpdatePropertyCommand

class PropertyPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.api = APIManager.get_instance()
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0,0,0,0)
        
        self.header = QLabel("Properties")
        self.header.setStyleSheet("font-weight: bold; padding: 10px; background: #2c313a; color: white;")
        self.layout.addWidget(self.header)
        
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        from PySide6.QtWidgets import QSizePolicy
        self.content = QWidget()
        self.content.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        self.form = QFormLayout(self.content)
        self.scroll.setWidget(self.content)
        self.scroll.setWidgetResizable(True)
        self.layout.addWidget(self.scroll)
        
        # Subscribe to Selection Changes
        self.api.subscribe("selection_changed", self.on_selection_changed)
        self.api.subscribe("model_changed", self.refresh)
        
        self.current_item = None
        self.refresh()

    def on_selection_changed(self, data):
        # Use the event payload for selection
        sel = data.get('selection', [])
        import datetime
        ts = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
        # ...removed debug print...
        self.current_item = sel[0] if sel else None
        self.refresh()

    def refresh(self, data=None):
        # ...removed debug print...
        # Clear existing rows
        while self.form.count():
            child = self.form.takeAt(0)
            if child.widget(): child.widget().deleteLater()
        if not self.current_item:
            # ...removed debug print...
            self.form.addRow(QLabel("No Selection"))
            self.content.adjustSize()
            self.scroll.ensureVisible(0, 0, 1, 1)
            return
        model = self.current_item
        # ...removed debug print...
        # Route to specific renderer
        if isinstance(model, Device):
            # ...removed debug print...
            self._render_device(model)
        elif isinstance(model, Wire):
            # ...removed debug print...
            self._render_wire(model)
        elif isinstance(model, Pin):
            # ...removed debug print...
            self._render_pin(model) # <--- NEW HANDLER
        else:
            # ...removed debug print...
            self.form.addRow(QLabel(f"Unknown Item: {type(model).__name__}"))

    def _render_device(self, device):
        from core.metadata import MetadataManager
        meta_mgr = MetadataManager.get_instance()
        schema = meta_mgr.schemas.get(device.meta.get('_type', 'generic'), meta_mgr.schemas.get('generic'))
        self._add_field("ID", device.id, read_only=True)
        # Iterate over schema fields
        for key, field_def in schema.get('fields', {}).items():
            label = field_def.get('label', key)
            value = device.meta.get(key, field_def.get('default'))
            field_type = field_def.get('type', 'string')
            read_only = field_def.get('read_only', False)
            # Editor selection based on type (simple: string, float, int, select)
            if field_type == 'select':
                # For select fields, use a dropdown (QComboBox)
                from PySide6.QtWidgets import QComboBox
                combo = QComboBox()
                options = field_def.get('options', [])
                combo.addItems([str(opt) for opt in options])
                combo.setCurrentText(str(value))
                if not read_only:
                    combo.currentTextChanged.connect(lambda v, k=key: self._update_model(device, k, v))
                self.form.addRow(label, combo)
            else:
                # For other types, use QLineEdit
                self._add_field(label, value, (lambda v, k=key: self._update_model(device, k, v)) if not read_only else None, read_only)

    def _render_wire(self, wire):
        self._add_field("ID", wire.id, read_only=True)
        self._add_field("From", f"{wire.from_conn}:{wire.from_pin}", read_only=True)
        self._add_field("To", f"{wire.to_conn}:{wire.to_pin}", read_only=True)
        self._add_field("Color", wire.color, lambda v: self._update_model(wire, "color", v))
        self._add_field("Gauge", str(wire.gauge), lambda v: self._update_model(wire, "gauge", v))

    def _render_pin(self, pin):
        # --- NEW PIN RENDERER ---
        self._add_field("Pin ID", pin.id, read_only=True)
        self._add_field("Signal", pin.signal, lambda v: self._update_model(pin, "signal", v))
        
        # Calculate Absolute Position for reference
        self.form.addRow(QLabel("--- Geometry ---"))
        self._add_field("Rel X", str(pin.x), lambda v: self._update_model(pin, "x", float(v)))
        self._add_field("Rel Y", str(pin.y), lambda v: self._update_model(pin, "y", float(v)))

    def _add_field(self, label, value, callback=None, read_only=False):
        lbl = QLabel(label)
        edit = QLineEdit(str(value) if value is not None else "")
        if read_only:
            edit.setReadOnly(True)
            edit.setStyleSheet("color: gray;")
        elif callback:
            edit.editingFinished.connect(lambda: callback(edit.text()))
        
        self.form.addRow(lbl, edit)

    def _update_model(self, item, field, value):
        # Use Command Pattern
        cmd = UpdatePropertyCommand(item, field, value)
        self.api.context.undo_stack.push(cmd)