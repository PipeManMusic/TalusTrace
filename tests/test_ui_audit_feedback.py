import pytest
from unittest.mock import MagicMock
from ui.panels.audit import AuditPanel
from api.manager import APIManager

def test_audit_interactive_zoom(qtbot):
    """
    PH5-EDIT.2: Clicking an audit violation must trigger a zoom-to-item action.
    """
    # 1. Setup API & Mocks
    APIManager._instance = None # Reset singleton
    api = APIManager.get_instance()
    
    # Mock the API methods we expect to be called
    api.select = MagicMock()
    api.dispatch = MagicMock()
    
    # 2. Initialize Panel
    panel = AuditPanel()
    qtbot.add_widget(panel)
    panel.show()
    
    # 3. Simulate a violation on wire "W1"
    violation = {"id": "W1", "type": "BEND_RADIUS", "message": "Sharp turn detected"}
    
    # 4. Trigger the internal zoom handler
    # (In a real app, this would be connected to a button signal)
    panel.on_zoom_clicked(violation)
    
    # 5. Verify API Interactions
    
    # Assertion A: Item must be selected
    api.select.assert_called_once()
    # Check that the first argument (ids) contains "W1"
    # call_args returns (args, kwargs)
    args, kwargs = api.select.call_args
    assert args[0] == ["W1"] 
    assert kwargs.get("tool_name") == "AuditPanel"
    
    # Assertion B: Zoom request must be dispatched
    api.dispatch.assert_called()
    # Check specifically for the zoom request event
    # dispatch(event_name, data)
    # call.args returns the tuple of positional arguments
    dispatch_event_names = [call.args[0] for call in api.dispatch.call_args_list]
    assert "request_zoom_to_selection" in dispatch_event_names