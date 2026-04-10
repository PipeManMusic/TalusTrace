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
    This test verifies that api.select() correctly updates SelectionManager.
    """
    from api.manager import APIManager
    from core.harness import DeviceList
    
    api = APIManager.get_instance()
    
    dev = Device(id="11111111-1111-1111-1111-111111111111")
    with DeviceList.test_bypass():
        api.context.harness.devices.append(dev)
    
    # CORRECT FLOW: API drives selection
    api.select([dev.id])
    
    # Verify selection manager was updated
    from core.selection import SelectionManager
    assert dev.id in SelectionManager().current_selection_ids
    
    # Clean up
    SelectionManager().clear_selection()