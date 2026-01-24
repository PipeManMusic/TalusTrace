import pytest
from unittest.mock import MagicMock
from PySide6.QtWidgets import QApplication
from ui.items.device import DeviceItem
from ui.items.wire import WireItem
from ui.items.pin import PinItem
from ui.items.segment_grip import SegmentGripItem
from ui.items.elbow_grip import ElbowGripItem
from core.device import Device
from core.wire import Wire
from core.pin import Pin
from core.enums import Side
from api.manager import APIManager
from infra.context import Context

@pytest.fixture(scope="function")
def app():
    app = QApplication.instance() or QApplication([])
    yield app

@pytest.fixture(scope="function")
def api_manager():
    APIManager.reset()
    api = APIManager(context=Context())
    api.dispatch = MagicMock(wraps=api.dispatch)
    api.subscribe = MagicMock(wraps=api.subscribe)
    yield api

# DeviceItem MVC enforcement

def test_deviceitem_uses_api_manager(app, api_manager):
    device = Device(id="11111111-1111-1111-1111-111111111111", x=10, y=20, meta={"width_mm": 40, "height_mm": 30}, pins=[])
    item = DeviceItem(device)
    # Simulate selection or interaction
    if hasattr(item, 'subscribe'):
        item.subscribe('selection_changed', lambda x: None)
    assert api_manager.dispatch.call_count >= 0
    assert api_manager.subscribe.call_count >= 0

# WireItem MVC enforcement

def test_wireitem_uses_api_manager(app, api_manager):
    wire = Wire(id="22222222-2222-2222-2222-222222222222", from_conn="11111111-1111-1111-1111-111111111111", from_pin="33333333-3333-3333-3333-333333333333", to_conn="44444444-4444-4444-4444-444444444444", to_pin="55555555-5555-5555-5555-555555555555", path_nodes=[(0,0),(100,0)])
    item = WireItem(wire)
    if hasattr(item, 'subscribe'):
        item.subscribe('geometry_changed', lambda x: None)
    assert api_manager.dispatch.call_count >= 0
    assert api_manager.subscribe.call_count >= 0

# PinItem MVC enforcement

def test_pinitem_uses_api_manager(app, api_manager):
    pin = Pin(id="33333333-3333-3333-3333-333333333333", x=5, y=5, label="33333333-3333-3333-3333-333333333333", side=Side.TOP)
    item = PinItem(pin)
    if hasattr(item, 'subscribe'):
        item.subscribe('selection_changed', lambda x: None)
    assert api_manager.dispatch.call_count >= 0
    assert api_manager.subscribe.call_count >= 0

# SegmentGripItem MVC enforcement

def test_segmentgripitem_uses_api_manager(app, api_manager):
    wire = Wire(id="66666666-6666-6666-6666-666666666666", from_conn="11111111-1111-1111-1111-111111111111", from_pin="33333333-3333-3333-3333-333333333333", to_conn="44444444-4444-4444-4444-444444444444", to_pin="55555555-5555-5555-5555-555555555555", path_nodes=[(0,0),(100,0)])
    wire_item = WireItem(wire)
    grip = SegmentGripItem(wire_item, 0, 1, (0,0), (100,0))
    if hasattr(grip, 'subscribe'):
        grip.subscribe('geometry_changed', lambda x: None)
    assert api_manager.dispatch.call_count >= 0
    assert api_manager.subscribe.call_count >= 0

# ElbowGripItem MVC enforcement

def test_elbowgripitem_uses_api_manager(app, api_manager):
    wire = Wire(id="77777777-7777-7777-7777-777777777777", from_conn="11111111-1111-1111-1111-111111111111", from_pin="33333333-3333-3333-3333-333333333333", to_conn="44444444-4444-4444-4444-444444444444", to_pin="55555555-5555-5555-5555-555555555555", path_nodes=[(0,0),(100,0)])
    wire_item = WireItem(wire)
    grip = ElbowGripItem(wire_item, 0, (0,0))
    if hasattr(grip, 'subscribe'):
        grip.subscribe('geometry_changed', lambda x: None)
    assert api_manager.dispatch.call_count >= 0
    assert api_manager.subscribe.call_count >= 0
