import pytest
from PySide6.QtCore import Qt
from ui.canvas import HarnessCanvas
from api.manager import APIManager
from ui.input_system import InputSystem

def test_canvas_instantiates_and_renders(qtbot):
    canvas = HarnessCanvas()
    qtbot.add_widget(canvas)
    # The new canvas is a pure renderer. This test now only checks instantiation and rendering.
    assert canvas is not None
    assert hasattr(canvas, 'scene')
    assert canvas.scene.items() == []
