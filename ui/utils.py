from PySide6.QtCore import QPoint, QPointF

# Utility to get scene position from any mouse event
# Handles both view events and item events

def get_scene_pos(event, canvas=None):
    """
    Returns the scene position for a Qt mouse event.
    If event has scenePos(), use it directly (item event).
    Otherwise, map event.pos() (view event) using canvas.mapToScene.
    """
    if hasattr(event, 'scenePos'):
        return event.scenePos()
    elif hasattr(event, 'pos') and canvas is not None:
        pos = event.position().toPoint() if hasattr(event, 'position') else event.pos()
        return canvas.mapToScene(pos)
    else:
        raise ValueError("Cannot determine scene position from event.")
