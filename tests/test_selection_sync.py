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
    dev = Device(id="11111111-1111-1111-1111-111111111111")
    item = DeviceItem(dev)
    
    # Simulate Selection
    item.setSelected(True)
    # The itemChange event in DeviceItem should notify the Manager
    
    assert "11111111-1111-1111-1111-111111111111" in SelectionManager().current_selection_ids