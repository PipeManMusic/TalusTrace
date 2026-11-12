"""Headless tests for the MeasureTool ruler behaviour."""
from unittest.mock import MagicMock

from PySide6.QtCore import QPointF, Qt
from PySide6.QtWidgets import QGraphicsScene

from tools.measure_tool import MeasureTool


def _press(x, y):
    """Build a minimal left-button canvas event at scene position (x, y)."""
    event = MagicMock()
    event.scene_pos = QPointF(x, y)
    event.original_event.button.return_value = Qt.LeftButton
    return event


def _make_tool(fresh_api):
    """Create a MeasureTool wired to a real scene and identity snapping."""
    tool = MeasureTool()
    tool.api = fresh_api
    fresh_api.scene = QGraphicsScene()
    fresh_api.settings = MagicMock()
    fresh_api.settings.snap.side_effect = lambda v: v  # no snapping
    tool.start()
    return tool


def test_measure_two_clicks_reports_distance(qtbot, fresh_api):
    tool = _make_tool(fresh_api)

    # First click anchors the start point.
    tool.on_mouse_press(_press(0.0, 0.0))
    assert tool.start_point == QPointF(0.0, 0.0)
    assert tool._line_item is not None

    # Move to (30, 40): straight-line distance is 50 mm.
    tool.on_mouse_move(_press(30.0, 40.0))
    assert "50.0 mm" in tool._label_item.text()
    assert "Δx 30.0" in tool._label_item.text()
    assert "Δy 40.0" in tool._label_item.text()

    line = tool._line_item.line()
    assert (line.x1(), line.y1()) == (0.0, 0.0)
    assert (line.x2(), line.y2()) == (30.0, 40.0)

    # Second click finalizes and resets for the next measurement.
    tool.on_mouse_press(_press(30.0, 40.0))
    assert tool.start_point is None
    assert "50.0 mm" in tool._label_item.text()


def test_measure_snaps_endpoints_to_grid(qtbot, fresh_api):
    tool = MeasureTool()
    tool.api = fresh_api
    fresh_api.scene = QGraphicsScene()
    fresh_api.settings = MagicMock()
    fresh_api.settings.snap.side_effect = lambda v: round(v / 5.0) * 5.0
    tool.start()

    tool.on_mouse_press(_press(2.0, 2.0))  # snaps to (0, 0)
    assert tool.start_point == QPointF(0.0, 0.0)

    tool.on_mouse_move(_press(13.0, 8.0))  # snaps to (15, 10)
    line = tool._line_item.line()
    assert (line.x2(), line.y2()) == (15.0, 10.0)


def test_measure_deactivate_clears_overlay(qtbot, fresh_api):
    tool = _make_tool(fresh_api)
    tool.on_mouse_press(_press(0.0, 0.0))
    tool.on_mouse_move(_press(10.0, 0.0))
    assert len(fresh_api.scene.items()) == 2  # line + label

    tool.deactivate()
    assert tool._line_item is None
    assert tool._label_item is None
    assert fresh_api.scene.items() == []


def test_second_measurement_replaces_first(qtbot, fresh_api):
    tool = _make_tool(fresh_api)

    # Complete one measurement.
    tool.on_mouse_press(_press(0.0, 0.0))
    tool.on_mouse_move(_press(10.0, 0.0))
    tool.on_mouse_press(_press(10.0, 0.0))

    # Starting a new one must discard the previous ruler (no duplicate items).
    tool.on_mouse_press(_press(50.0, 50.0))
    assert tool.start_point == QPointF(50.0, 50.0)
    assert len(fresh_api.scene.items()) == 2  # still just one line + one label


def test_measure_tool_command_activates_tool(clean_api_singleton):
    api = clean_api_singleton
    api.measure_tool()
    assert api.tool_manager.active_tool is api.tool_manager.get_tool("measure")
    assert api.tool_manager.active_tool.__class__.__name__ == "MeasureTool"
