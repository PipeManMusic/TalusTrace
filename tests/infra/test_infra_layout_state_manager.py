import pytest
from infra.layout_state_manager import LayoutStateManager

def test_layout_state_manager_basic():
    layout = LayoutStateManager()
    layout.set_window('main', x=10, y=20, width=800, height=600)
    layout.set_panel('sidebar', visible=True, width=250)
    layout.push_navigation('dashboard')
    layout.push_navigation('settings')
    assert layout.get_window('main')['width'] == 800
    assert layout.get_panel('sidebar')['visible'] is True
    assert layout.navigation == ['dashboard', 'settings']
    popped = layout.pop_navigation()
    assert popped == 'settings'
    assert layout.navigation == ['dashboard']

def test_layout_state_manager_serialize():
    layout = LayoutStateManager()
    layout.set_window('main', x=1, y=2, width=3, height=4)
    layout.set_panel('footer', visible=False, height=50)
    layout.push_navigation('home')
    state = layout.serialize()
    layout2 = LayoutStateManager.deserialize(state)
    assert layout2.get_window('main')['x'] == 1
    assert layout2.get_panel('footer')['height'] == 50
    assert layout2.navigation == ['home']
