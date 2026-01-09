import pytest
from unittest.mock import MagicMock
from ui.panels.audit import AuditPanel
from api.manager import APIManager

def test_audit_zoom_interaction(qtbot):
    """PH5-EDIT.2: Clicking an error should trigger zoom action."""
    api = APIManager.get_instance()
    api.dispatch = MagicMock()
    
    panel = AuditPanel()
    qtbot.add_widget(panel)
    
    # Mock Violation Data
    violation = {"id": "W1", "message": "Bend Radius"}
    
    # Simulate clicking the "Zoom" button for this violation
    # (Assuming internal method calls API)
    panel.on_zoom_clicked(violation)
    
    # Verify 'view.zoom_to' event dispatched
    assert api.dispatch.called
    args = api.dispatch.call_args
    assert args[0][0] == "view.zoom_to"
    assert args[0][1]["target_id"] == "W1"