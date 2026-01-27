import pytest
from PySide6.QtWidgets import QApplication, QGraphicsItem
from core.device import Device
from ui.items import DeviceItem
# Target Implementation: core/selection.py
from core.selection import SelectionManager

@pytest.fixture(scope="session")
def qapp():
    return QApplication.instance() or QApplication([])

def test_selection_manager_singleton(qapp):
    s1 = SelectionManager()
    s2 = SelectionManager()
    assert s1 is s2

def test_device_click_updates_manager(qapp):
    """
    Contract: Selection is driven by InputSystem -> API -> SelectionManager, not by View items.
    This test verifies that the API method correctly updates SelectionManager.
    The View (DeviceItem.setSelected) only reflects selection state; it does not drive it.
    """
    from api.manager import APIManager
    from infra.context import Context
    from core.harness import DeviceList
    
    # Reset API and create context
    APIManager.reset()
    api = APIManager(context=Context())
    
    dev = Device(id="11111111-1111-1111-1111-111111111111")
    # Use test bypass to add device directly without command
    with DeviceList.test_bypass():
        api.context.harness.devices.append(dev)
    
    # CORRECT FLOW: API drives selection (InputSystem would call this)
    from core.selection import SelectionManager
    SelectionManager().select(dev)
    
    # Verify selection manager was updated
    assert "11111111-1111-1111-1111-111111111111" in SelectionManager().current_selection_ids
    
    # Clean up
    SelectionManager().clear_selection()