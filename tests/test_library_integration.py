import pytest
from unittest.mock import MagicMock
from PySide6.QtCore import QMimeData, QPoint, Qt
from PySide6.QtGui import QDropEvent
from api.manager import APIManager
from ui.canvas import HarnessCanvas
from core.library_manager import LibraryManager

def test_library_drag_to_canvas_insertion(qtbot, clean_api_singleton):
    """
    Verifies that dragging an item from the Library and dropping it 
    onto the Canvas successfully inserts it into the Model.
    """
    # 1. Setup API and Canvas
    api = clean_api_singleton
    
    # Inject a Mock Library Manager with our test part
    # This ensures the test passes even if parts.yaml is missing the specific entry
    api.library = MagicMock(spec=LibraryManager)
    test_part_id = "TEST-SPLICE-001"
    test_part_def = {
        "manufacturer": "TestCorp",
        "category": "Splices",
        "pins": [{"id": "1"}, {"id": "2"}]
    }
    
    # Mock the get_parts() return
    api.library.get_parts.return_value = {test_part_id: test_part_def}
    
    canvas = HarnessCanvas()
    qtbot.add_widget(canvas)
    
    # Install the Input System (Crucial: The Canvas delegates drop to this)
    if api.input_system:
        api.input_system.install(canvas)
    
    # 2. Simulate the Drag Event
    # The LibraryPanel encodes data as "library://<device_id>"
    mime_data = QMimeData()
    mime_data.setText(f"library://{test_part_id}")
    
    # 3. Perform Drop at (100, 100)
    drop_pos = QPoint(100, 100)
    event = QDropEvent(drop_pos, Qt.CopyAction, mime_data, Qt.LeftButton, Qt.NoModifier)
    
    # Trigger the event handler directly
    canvas.dropEvent(event)
    
    # 4. Verification
    # Check if the device was added to the harness model
    devices = api.context.harness.devices
    
    assert len(devices) > 0, "Drop event failed to instantiate a device."
    
    new_device = devices[-1] 
    assert new_device.library_id == test_part_id, \
        f"Wrong device inserted. Expected {test_part_id}, got {new_device.library_id}"
    
    # Check position (approximate)
    assert abs(new_device.x - 100) < 1.0, "Device X position incorrect"
    assert abs(new_device.y - 100) < 1.0, "Device Y position incorrect"