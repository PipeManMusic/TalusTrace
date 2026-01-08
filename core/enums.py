from enum import Enum

class Side(str, Enum):
    """
    Defines the cardinal orientation of a Pin relative to its parent Device.
    """
    LEFT = "left"
    RIGHT = "right"
    TOP = "top"
    BOTTOM = "bottom"