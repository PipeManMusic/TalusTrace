import pytest
from PySide6.QtWidgets import QApplication
from talustrace.backend.models import Device
from talustrace.frontend.items import DeviceItem

# Fixture to ensure GUI context exists
@pytest.fixture(scope="session")
def qapp():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app

def test_device_item_creation(qapp):
    """Verify visual item is created from model data."""
    # 1. Create Data Model
    model = Device(id="D1", label="ECU", pins=10, x=100, y=200)

    # 2. Create Visual Item
    item = DeviceItem(model)

    # 3. Check Visual Properties
    # Did it read the position correctly?
    assert item.pos().x() == 100
    assert item.pos().y() == 200
    
    # Did it set the text label?
    assert item.label.text() == "ECU"
    
    # Did it calculate a reasonable height for 10 pins?
    rect = item.rect()
    assert rect.height() > 0
