import pytest
from PySide6.QtWidgets import QDialogButtonBox
from PySide6.QtCore import Qt
from ui.panels.mapping import PinMappingDialog # PH4-3.1 Implementation target

def test_ph4_3_1_pin_mapping_interaction(qtbot):
    """
    Validates user assignment of a wire end to a connector pin.
    """
    # Setup mock wire and connector
    mock_wire_id = "W_POWER_01"
    mock_connector_id = "J_MAIN_ECU"
    
    dialog = PinMappingDialog(wire_id=mock_wire_id, connector_id=mock_connector_id)
    qtbot.add_widget(dialog)
    
    # Simulate selecting Pin "1:A" from a list or combo box
    qtbot.keyClicks(dialog.pin_selector, "1:A")
    
    # Click OK to accept the mapping
    ok_button = dialog.button_box.button(QDialogButtonBox.StandardButton.Ok)
    qtbot.mouseClick(ok_button, Qt.MouseButton.LeftButton)
    
    assert dialog.result() == PinMappingDialog.DialogCode.Accepted
    assert dialog.get_selected_pin() == "1:A"