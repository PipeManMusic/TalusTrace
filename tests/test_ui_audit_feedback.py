from unittest.mock import MagicMock
from ui.panels.audit import AuditPanel
from api.manager import APIManager

def test_audit_interactive_zoom(qtbot):
    """
    PH5-EDIT.2: Clicking an audit violation must trigger a zoom-to-item action.
    """
    api = APIManager.get_instance()
    api.dispatch = MagicMock()
    
    panel = AuditPanel()
    qtbot.add_widget(panel)
    
    # Simulate a violation on wire "W1"
    violation = {"id": "W1", "type": "BEND_RADIUS", "message": "Sharp turn detected"}
    
    # Trigger the internal zoom handler
    panel.on_zoom_clicked(violation)
    
    # Verify the API dispatch call
    api.dispatch.assert_called_with("view.zoom_to", {"target_id": "W1"})