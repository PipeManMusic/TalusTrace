import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication
from ui.canvas import HarnessCanvas

def test_canvas_scroll_zoom(qtbot):
    """PH6-UI.7: Scrolling mouse wheel should zoom in/out the canvas."""
    app = QApplication.instance() or QApplication([])
    canvas = HarnessCanvas()
    qtbot.add_widget(canvas)
    canvas.show()
    # Initial scale
    initial_transform = canvas.transform().m11()
    # Simulate wheel event (zoom in)
    from PySide6.QtGui import QWheelEvent
    from PySide6.QtCore import QPoint, QPointF, Qt
    # Zoom in
    event_in = QWheelEvent(
        QPointF(100, 100), QPointF(100, 100), QPoint(0, 0), QPoint(0, 120),
        Qt.NoButton, Qt.NoModifier, Qt.ScrollUpdate, False
    )
    canvas.wheelEvent(event_in)
    zoomed_transform = canvas.transform().m11()
    assert zoomed_transform > initial_transform, f"Canvas did not zoom in on wheel scroll: {zoomed_transform} <= {initial_transform}"
    # Zoom out
    event_out = QWheelEvent(
        QPointF(100, 100), QPointF(100, 100), QPoint(0, 0), QPoint(0, -120),
        Qt.NoButton, Qt.NoModifier, Qt.ScrollUpdate, False
    )
    canvas.wheelEvent(event_out)
    zoomed_out_transform = canvas.transform().m11()
    assert zoomed_out_transform < zoomed_transform, f"Canvas did not zoom out on wheel scroll: {zoomed_out_transform} >= {zoomed_transform}"
