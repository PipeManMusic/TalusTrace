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
    
    # Patch APIManager to verify drag/drop handler calls
    api.handle_drag_enter = MagicMock()
    api.handle_drop = MagicMock()
    # 2. Create Canvas
    canvas = HarnessCanvas()
    qtbot.addWidget(canvas)
    # 3. Simulate Drop Event
    mime = QMimeData()
    mime.setText("library://generic/connector_2pin")
    drag_evt = QDragEnterEvent(QPoint(10, 10), Qt.CopyAction, mime, Qt.LeftButton, Qt.NoModifier)
    drop_evt = QDropEvent(QPoint(10, 10), Qt.CopyAction, mime, Qt.LeftButton, Qt.NoModifier)
    canvas.dragEnterEvent(drag_evt)
    if not drag_evt.isAccepted():
        pytest.fail("Canvas rejected DragEnter - Drop logic unreachable.")
    canvas.dropEvent(drop_evt)
    api.handle_drag_enter.assert_called_once_with(drag_evt)
    api.handle_drop.assert_called_once_with(drop_evt)
