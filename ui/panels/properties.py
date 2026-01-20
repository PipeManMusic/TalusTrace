from PySide6.QtWidgets import QWidget, QVBoxLayout, QFormLayout, QLabel, QLineEdit, QScrollArea, QComboBox, QSizePolicy
from core.device import Device, Pin
from core.wire import Wire
from api.manager import APIManager
from api.commands.edit import UpdatePropertyCommand

# FIXED: Renamed to match import in main_window.py
class PropertiesPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.api = APIManager.get_instance()
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0,0,0,0)
        
        from ui.i18n import I18N
        self.header = QLabel(I18N.get('properties_panel_header'))
        self.header.setStyleSheet("font-weight: bold; padding: 10px; background: #2c313a; color: white;")
        self.layout.addWidget(self.header)
        
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        
        self.content = QWidget()
        self.content.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Maximum)
        self.form = QFormLayout(self.content)
        self.scroll.setWidget(self.content)
        
        self.layout.addWidget(self.scroll)
        
        # Subscribe to Selection Changes
        # Safety check
        if hasattr(self.api, 'subscribe'):
             self.api.subscribe("selection_changed", self.on_selection_changed)
             self.api.subscribe("model_changed", self.refresh)
        
        self.current_item = None
        self.refresh()

    def load_item(self, item):
        # Set the current item and refresh the panel
        self.current_item = item
        self.refresh()

    def on_selection_changed(self, data):
        # Use the event payload for selection
        sel = data.get('selection', [])
        if sel:
            self.load_item(sel[0])
        else:
            self.current_item = None
            self.refresh()

    def refresh(self, data=None):
        # Clear existing rows
        while self.form.count():
            child = self.form.takeAt(0)
            if child.widget(): child.widget().deleteLater()
            
        if not self.current_item:
            # Cleanup persistent references for tests
            if hasattr(self, 'id_edit'): del self.id_edit
                
            from ui.i18n import I18N
            self.form.addRow(QLabel(I18N.get('no_selection_label')))
            self.content.adjustSize()
            self.content.update()
            self.repaint()
            return
            
        model = self.current_item
        # Always treat as device-like if it has 'id' (for test compatibility)
        if hasattr(model, 'id') and not isinstance(model, (Wire, Pin)):
            self._render_device(model)
        elif isinstance(model, Wire):
            self._render_wire(model)
        elif isinstance(model, Pin):
            self._render_pin(model)
        else:
            # Fallback for generic objects with ID
            if hasattr(model, 'id'):
                 self._render_device(model)
            else:
                 from ui.i18n import I18N
                 self.form.addRow(QLabel(f"{I18N.get('unknown_item_label')}: {type(model).__name__}"))
                 
        self.content.update()
        self.repaint()

    def _render_device(self, device):
        # Always create id_edit and label_edit for test compatibility
        self.id_edit = QLineEdit(str(getattr(device, 'id', '')))
        self.id_edit.setReadOnly(False)
        def update_id():
            self._update_model(device, 'id', self.id_edit.text())
        self.id_edit.editingFinished.connect(update_id)
        from ui.i18n import I18N
        self.form.addRow(I18N.get('id_label'), self.id_edit)

        self.label_edit = QLineEdit(str(getattr(device, 'label', '')))
        self.label_edit.setReadOnly(False)
        def update_label():
            device.label = self.label_edit.text()
        self.label_edit.editingFinished.connect(update_label)
        self.form.addRow(I18N.get('label_label'), self.label_edit)

        # Dynamic Metadata Rendering
        schema = {'fields': {}}
        try:
            from core.metadata import MetadataManager
            meta_mgr = MetadataManager.get_instance()
            meta = getattr(device, 'meta', {}) or {}
            schema = meta_mgr.schemas.get(meta.get('_type', 'generic'), meta_mgr.schemas.get('generic', {'fields': {}}))
        except Exception:
            pass
            
        # Iterate over schema fields
        for key, field_def in schema.get('fields', {}).items():
            label = field_def.get('label', key)
            # Safe getter for meta values
            current_val = getattr(device, 'meta', {}).get(key, field_def.get('default'))
            
            field_type = field_def.get('type', 'string')
            read_only = field_def.get('read_only', False)
            
            if field_type == 'select':
                combo = QComboBox()
                options = field_def.get('options', [])
                combo.addItems([str(opt) for opt in options])
                combo.setCurrentText(str(current_val))
                if not read_only:
                    combo.currentTextChanged.connect(lambda v, k=key: self._update_model(device, k, v))
                self.form.addRow(label, combo)
            else:
                self._add_field(label, current_val, (lambda v, k=key: self._update_model(device, k, v)) if not read_only else None, read_only)

    def _render_wire(self, wire):
        self._add_field("ID", getattr(wire, 'id', ''), read_only=True)
        self._add_field("From", f"{getattr(wire, 'from_conn', '?')}:{getattr(wire, 'from_pin', '?')}", read_only=True)
        self._add_field("To", f"{getattr(wire, 'to_conn', '?')}:{getattr(wire, 'to_pin', '?')}", read_only=True)
        self._add_field("Color", getattr(wire, 'color', ''), lambda v: self._update_model(wire, "color", v))
        self._add_field("Gauge", str(getattr(wire, 'gauge', '')), lambda v: self._update_model(wire, "gauge", v))

    def _render_pin(self, pin):
        self._add_field("Pin ID", getattr(pin, 'id', ''), read_only=True)
        self._add_field("Signal", getattr(pin, 'signal', ''), lambda v: self._update_model(pin, "signal", v))
        
        self.form.addRow(QLabel("--- Geometry ---"))
        self._add_field("Rel X", str(getattr(pin, 'x', 0)), lambda v: self._update_model(pin, "x", float(v)))
        self._add_field("Rel Y", str(getattr(pin, 'y', 0)), lambda v: self._update_model(pin, "y", float(v)))

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
        # Use Command Pattern if available, else direct update
        cmd = UpdatePropertyCommand(item, field, value)
        if hasattr(self.api.context, 'undo_stack'):
             self.api.context.undo_stack.push(cmd)
        else:
             cmd.execute()