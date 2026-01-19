import pytest
from unittest.mock import MagicMock
from ui.canvas import HarnessCanvas
from api.manager import APIManager

@pytest.fixture
def canvas(qtbot):
    c = HarnessCanvas()
    qtbot.addWidget(c)
    c.show()
    return c

@pytest.fixture
def api_manager():
    APIManager.reset()
    return APIManager()

# Contract: Context menu activation triggers APIManager.open_context_menu and updates state
def test_context_menu_action_contract(canvas, api_manager, monkeypatch):
    monkeypatch.setattr(APIManager, 'get_instance', lambda: api_manager)
    api_manager.open_context_menu = MagicMock()
    # Simulate right-click/context menu event
    from PySide6.QtGui import QContextMenuEvent
    from PySide6.QtCore import QPoint, Qt
    event = QContextMenuEvent(QContextMenuEvent.Mouse, QPoint(10, 10), QPoint(10, 10), Qt.NoModifier)
    canvas.contextMenuEvent(event)
    api_manager.open_context_menu.assert_called_once_with(event)
