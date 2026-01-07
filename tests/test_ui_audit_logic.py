import pytest
from unittest.mock import patch
from api.audit_controller import AuditController

def test_audit_selection_dispatch():
    """
    Validates PH3-3.2: UI: Persistent Audit Punch-List Panel logic.
    Ensures selecting a violation issues a focus/zoom command via the API 
    without requiring a QWidget or active display.
    """
    controller = AuditController()
    mock_violation = {"target_id": "wire_55", "message": "High Current"}
    
    with patch("api.manager.APIManager.dispatch") as mock_dispatch:
        # Simulate selecting an item (logic only)
        controller.select_violation(mock_violation)
        
        # Verify the FOCUS_ENTITY transaction is issued correctly
        mock_dispatch.assert_called_once_with(
            "FOCUS_ENTITY", 
            {"id": "wire_55", "zoom_level": 1.5}
        )