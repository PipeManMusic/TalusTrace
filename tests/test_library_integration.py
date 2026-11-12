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
        api.input_system = InputSystem()
        
    # 2. Setup Mock Library
    # We inject the part definition so the API can find it
    api.library = MagicMock(spec=LibraryManager)
    import uuid
    test_part_id = str(uuid.uuid4())
    test_pin_id = str(uuid.uuid4())
    test_part_def = {
        "manufacturer": "TestCorp", 
        "category": "Splices",
        "width_mm": 12.0,
        "height_mm": 6.0,
        "pins": [{"id": test_pin_id}]
    }
    test_svg = "<?xml version='1.0' encoding='UTF-8'?><svg xmlns='http://www.w3.org/2000/svg' width='12' height='6'><rect x='0' y='0' width='12' height='6' fill='#000000'/></svg>"
    test_part_def["svg_body"] = test_svg
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
    assert devices[-1].svg_body == test_svg
    assert devices[-1].meta["width_mm"] == 12.0
    assert devices[-1].meta["height_mm"] == 6.0
    # Check approximate position (float precision)
    assert abs(devices[-1].x - 100) < 1.0


def _make_library_api(clean_api_singleton):
    """Wire a mock library with one SVG part onto the clean API singleton."""
    api = clean_api_singleton
    if not api.input_system:
        api.input_system = InputSystem()
    api.library = MagicMock(spec=LibraryManager)
    import uuid
    part_id = str(uuid.uuid4())
    part_def = {
        "manufacturer": "TestCorp",
        "category": "Splices",
        "width_mm": 12.0,
        "height_mm": 6.0,
        "pins": [{"id": str(uuid.uuid4())}],
        "svg_body": (
            "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 12 6'>"
            "<rect x='0' y='0' width='12' height='6' fill='#000'/></svg>"
        ),
    }
    api.library.get_parts.return_value = {part_id: part_def}
    return api, part_id, part_def


def test_make_drag_ghost_device_carries_svg_and_dimensions(clean_api_singleton):
    """The ghost factory returns an unattached Device with svg + dimensions."""
    api, part_id, part_def = _make_library_api(clean_api_singleton)

    ghost = api.make_drag_ghost_device(f"library://{part_id}")

    assert ghost is not None
    assert ghost.library_id == part_id
    assert ghost.svg_body == part_def["svg_body"]
    assert ghost.meta["width_mm"] == 12.0
    assert ghost.meta["height_mm"] == 6.0
    # Must NOT be added to the harness — it is a throwaway preview model.
    assert ghost not in api.context.harness.devices


def test_make_drag_ghost_device_rejects_non_library_mime(clean_api_singleton):
    """Non-library mime text yields no ghost model."""
    api, _part_id, _ = _make_library_api(clean_api_singleton)
    assert api.make_drag_ghost_device("text/plain not a part") is None
    assert api.make_drag_ghost_device("") is None


def test_drag_move_shows_ghost_and_drop_clears_it(qtbot, clean_api_singleton):
    """Dragging over the canvas shows a ghost; dropping removes it."""
    from PySide6.QtGui import QDragMoveEvent, QDropEvent
    from PySide6.QtCore import QPointF

    api, part_id, _ = _make_library_api(clean_api_singleton)
    canvas = HarnessCanvas()
    qtbot.add_widget(canvas)
    api.view = canvas

    mime = QMimeData()
    mime.setText(f"library://{part_id}")

    move = QDragMoveEvent(
        QPoint(50, 50), Qt.CopyAction, mime, Qt.LeftButton, Qt.NoModifier
    )
    canvas.dragMoveEvent(move)

    ghost = canvas._drag_ghost
    assert ghost is not None, "Drag move did not create a ghost preview."
    assert ghost.is_ghost is True
    assert ghost in canvas.scene.items()

    drop = QDropEvent(
        QPointF(50, 50), Qt.CopyAction, mime, Qt.LeftButton, Qt.NoModifier
    )
    canvas.dropEvent(drop)

    assert canvas._drag_ghost is None, "Ghost was not cleared on drop."
    assert ghost not in canvas.scene.items()
    # And the real device was placed.
    assert any(d.library_id == part_id for d in api.context.harness.devices)


def test_drag_leave_clears_ghost(qtbot, clean_api_singleton):
    """Leaving the canvas mid-drag removes the ghost preview."""
    from PySide6.QtGui import QDragMoveEvent, QDragLeaveEvent

    api, part_id, _ = _make_library_api(clean_api_singleton)
    canvas = HarnessCanvas()
    qtbot.add_widget(canvas)
    api.view = canvas

    mime = QMimeData()
    mime.setText(f"library://{part_id}")
    canvas.dragMoveEvent(
        QDragMoveEvent(QPoint(10, 10), Qt.CopyAction, mime, Qt.LeftButton, Qt.NoModifier)
    )
    assert canvas._drag_ghost is not None

    canvas.dragLeaveEvent(QDragLeaveEvent())
    assert canvas._drag_ghost is None
