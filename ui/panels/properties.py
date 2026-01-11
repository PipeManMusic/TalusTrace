from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QLabel, QLineEdit, 
    QScrollArea, QFrame, QDoubleSpinBox
)
from api.manager import APIManager
from api.commands.edit import UpdatePropertyCommand
from core.device import Device
from core.wire import Wire

class PropertyPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Properties")
        
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0,0,0,0)
        
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.content_widget = QWidget()
        self.form_layout = QFormLayout(self.content_widget)
        self.scroll.setWidget(self.content_widget)
        self.layout.addWidget(self.scroll)
        
        self.clear_panel()
        
        # FIX: Correct 2-argument subscription
        APIManager.get_instance().subscribe("selection_changed", self._on_selection_changed)

    def _on_selection_changed(self, data):
        try:
            if not self.isVisible(): return
            selection = data.get("selection", [])
            if selection:
                self.load_item(selection[0])
            else:
                self.clear_panel()
        except RuntimeError: pass

    def clear_panel(self):
        self._clear_layout()
        self.form_layout.addRow(QLabel("No Selection"))

    def _clear_layout(self):
        while self.form_layout.count():
            item = self.form_layout.takeAt(0)
            widget = item.widget()
            if widget: widget.deleteLater()

    def load_item(self, item):
        self._clear_layout()
        
        if isinstance(item, Device):
            self._add_header(f"Device: {item.id}")
            self._add_text("Label", item, "label")
            self._add_spin("X", item, "x")
            self._add_spin("Y", item, "y")
            
            # FIX: The loop that was missing
            if hasattr(item, "meta") and item.meta:
                self._add_header("Parameters")
                for key, val in item.meta.items():
                    if key.startswith("_"): continue
                    if isinstance(val, (int, float)):
                        self._add_meta_spin(key, item, key)
                    else:
                        self._add_meta_text(key, item, key)

    def _add_header(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet("font-weight: bold; background: #444; padding: 4px; color: white;")
        self.form_layout.addRow(lbl)

    def _commit(self, target, field, value):
        cmd = UpdatePropertyCommand(target, field, value)
        APIManager.get_instance().context.undo_stack.push(cmd)

    def _add_text(self, label, obj, field):
        val = getattr(obj, field, "")
        w = QLineEdit(str(val))
        w.editingFinished.connect(lambda: self._commit(obj, field, w.text()))
        self.form_layout.addRow(label, w)

    def _add_spin(self, label, obj, field):
        val = getattr(obj, field, 0.0)
        w = QDoubleSpinBox()
        w.setRange(-99999, 99999)
        w.setValue(float(val))
        w.setButtonSymbols(QDoubleSpinBox.NoButtons)
        w.editingFinished.connect(lambda: self._commit(obj, field, w.value()))
        self.form_layout.addRow(label, w)

    def _add_meta_text(self, label, obj, key):
        val = obj.meta.get(key, "")
        w = QLineEdit(str(val))
        w.editingFinished.connect(lambda: self._commit(obj.meta, key, w.text()))
        self.form_layout.addRow(label.title(), w)

    def _add_meta_spin(self, label, obj, key):
        val = obj.meta.get(key, 0.0)
        w = QDoubleSpinBox()
        w.setRange(-99999, 99999)
        w.setValue(float(val))
        w.setButtonSymbols(QDoubleSpinBox.NoButtons)
        w.editingFinished.connect(lambda: self._commit(obj.meta, key, w.value()))
        self.form_layout.addRow(label.title(), w)
