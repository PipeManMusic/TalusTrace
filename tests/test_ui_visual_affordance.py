import pytest
from ui.items import DeviceItem
from core.device import Device
from PySide6.QtWidgets import QGraphicsDropShadowEffect

def test_selection_halo_logic():
    dev = Device(id="H", x=0, y=0)
    item = DeviceItem(dev)
    
    # Setting selection on the QGraphicsItem should trigger our effect logic
    item.setSelected(True)
    item.update_visual_state() 
    
    effect = item.graphicsEffect()
    assert isinstance(effect, QGraphicsDropShadowEffect)
    assert effect.blurRadius() > 0