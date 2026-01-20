import pytest
from unittest.mock import MagicMock
from PySide6.QtCore import QPoint, QMimeData, Qt
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from ui.canvas import HarnessCanvas
from api.manager import APIManager

def test_canvas_drop_routing_compliance(qtbot):
    """
    Compliance Check: PH4-UI (Hardware Abstraction Layer).
    
    Current Behavior (Risk): Canvas.dropEvent might parse MIME data and create Devices directly.
    Expected Behavior (Compliant): Canvas wraps event in CanvasEvent and sends to InputSystem.
    """
    # 1. Setup API & Mocks
    APIManager.reset()
    api = APIManager.get_instance()
    
    # Mock InputSystem to verify handoff
    mock_input = MagicMock()
    api.input_system = mock_input
    
    # 2. Create Canvas
    canvas = HarnessCanvas()
    qtbot.addWidget(canvas)
    
    # 3. Simulate Drop Event
    mime = QMimeData()
    mime.setText("library://generic/connector_2pin")
    
    # Create Qt Events (Mocking the drag/drop lifecycle)
    drag_evt = QDragEnterEvent(QPoint(10, 10), Qt.CopyAction, mime, Qt.LeftButton, Qt.NoModifier)
    drop_evt = QDropEvent(QPoint(10, 10), Qt.CopyAction, mime, Qt.LeftButton, Qt.NoModifier)
    
    # 4. Action: Drag Enter & Drop
    # (Canvas must accept drag for drop to happen)
    canvas.dragEnterEvent(drag_evt)
    if not drag_evt.isAccepted():
        pytest.fail("Canvas rejected DragEnter - Drop logic unreachable.")
        
    canvas.dropEvent(drop_evt)
    
    # 5. Critical Assertion: Delegation
    # Did the InputSystem get the call?
    assert mock_input.handle_canvas_event.called, \
        "VIOLATION: Canvas handled Drop Event internally! It must delegate to InputSystem."
        
    # Check Payload
    call_args = mock_input.handle_canvas_event.call_args
    event_obj = call_args[0][0]
    assert event_obj.type == "DROP", "Event type should be 'DROP'"
    assert event_obj.mime_data.text() == "library://generic/connector_2pin"
