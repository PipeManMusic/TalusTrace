import pytest
from PySide6.QtWidgets import QLineEdit
from api.manager import APIManager
from core.device import Device
from ui.panels.properties import PropertiesPanel

# Regression: Canvas deselection clears selection and panel

def test_canvas_deselection_clears_panel(qtbot):
    APIManager._instance = None
    api = APIManager.get_instance()
    panel = PropertiesPanel()
    qtbot.add_widget(panel)
    panel.show()
    import uuid
    dev = Device(id=str(uuid.uuid4()), label="Test")
    api.dispatch("selection_changed", {"selection": [dev]})
    qtbot.waitUntil(lambda: hasattr(panel, 'id_edit') and panel.id_edit.text() == dev.id, timeout=2000)
    # Simulate deselection
    api.dispatch("selection_changed", {"selection": []})
    qtbot.waitUntil(lambda: not hasattr(panel, 'id_edit') or not panel.id_edit.isVisible(), timeout=2000)
    assert not hasattr(panel, 'id_edit') or not panel.id_edit.isVisible()

# Regression: Property changes via panel are undoable and go through API

def test_property_panel_change_is_undoable(qtbot):
    APIManager._instance = None
    api = APIManager.get_instance()
    import uuid
    dev = Device(id=str(uuid.uuid4()), label="Test")
    panel = PropertiesPanel()
    qtbot.add_widget(panel)
    panel.show()
    api.dispatch("selection_changed", {"selection": [dev]})
    qtbot.waitUntil(lambda: hasattr(panel, 'label_edit'), timeout=2000)
    # Change label via panel
    panel.label_edit.setText("Changed")
    panel.label_edit.editingFinished.emit()
    assert dev.label == "Changed"
    # Undo via API
    api.context.undo_stack.undo()
    assert dev.label == "Test"
    # Redo via API
    api.context.undo_stack.redo()
    assert dev.label == "Changed"
