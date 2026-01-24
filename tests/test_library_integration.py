import pytest
from unittest.mock import MagicMock
from PySide6.QtCore import QMimeData, QPoint, Qt
from PySide6.QtGui import QDropEvent
from ui.canvas import HarnessCanvas
from core.library_manager import LibraryManager
from ui.input_system import InputSystem

def test_library_drag_to_canvas_insertion(qtbot, clean_api_singleton):
    """
    Verifies that dragging an item from the Library and dropping it 
    onto the Canvas successfully inserts it into the Model.
    """
    api = clean_api_singleton
    
    # 1. Setup Input System
    # The Canvas needs this to handle drops!
    if not api.input_system:
        api.input_system = InputSystem(api.context)
        
    # 2. Setup Mock Library
    # We inject the part definition so the API can find it
    api.library = MagicMock(spec=LibraryManager)
    import uuid
    test_part_id = str(uuid.uuid4())
    test_pin_id = str(uuid.uuid4())
    test_part_def = {
        "manufacturer": "TestCorp", 
        "category": "Splices",
        "pins": [{"id": test_pin_id}]
    }
    api.library.get_parts.return_value = {test_part_id: test_part_def}
    
    # 3. Setup Canvas
    canvas = HarnessCanvas()
    qtbot.add_widget(canvas)
    
    # CRITICAL: Wire the InputSystem to the Canvas
    # This ensures dropEvent delegates to the InputSystem -> Tools
    api.input_system.install(canvas)
    
    # 4. Simulate Drop
    mime_data = QMimeData()
    mime_data.setText(f"library://{test_part_id}")
    
    drop_pos = QPoint(100, 100)
    event = QDropEvent(drop_pos, Qt.CopyAction, mime_data, Qt.LeftButton, Qt.NoModifier)
    
    # Manually trigger the drop logic
    canvas.dropEvent(event)
    
    # 5. Verification
    devices = api.context.harness.devices
    assert len(devices) > 0, "Drop event failed to instantiate a device."
    assert devices[-1].library_id == test_part_id
    # Check approximate position (float precision)
    assert abs(devices[-1].x - 100) < 1.0