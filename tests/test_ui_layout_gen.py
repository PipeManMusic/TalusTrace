import pytest
import yaml
from PySide6.QtWidgets import QApplication, QMainWindow, QToolBar
from api.actions import registry, register_action
# Target Implementation: ui/layout_manager.py
from ui.layout_manager import LayoutManager

@pytest.fixture(scope="session")
def qapp():
    return QApplication.instance() or QApplication([])

@pytest.fixture
def temp_layout_config(tmp_path):
    config = {
        "toolbar": {
            "visible": True,
            "items": [{"command": "test.cmd1"}, {"separator": True}, {"command": "test.cmd2"}]
        }
    }
    path = tmp_path / "ui_layout.yaml"
    with open(path, 'w') as f:
        yaml.dump(config, f)
    return str(path)

def test_toolbar_generation(qapp, temp_layout_config):
    @register_action("test.cmd1")
    def cmd1(ctx): pass
    @register_action("test.cmd2")
    def cmd2(ctx): pass

    window = QMainWindow()
    manager = LayoutManager(config_path=temp_layout_config)
    toolbar = manager.create_toolbar(window)
    
    assert isinstance(toolbar, QToolBar)
    actions = toolbar.actions()
    assert len(actions) == 3
    assert actions[0].data() == "test.cmd1"
    assert actions[1].isSeparator()