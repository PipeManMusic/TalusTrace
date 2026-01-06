from PySide6.QtWidgets import QApplication, QGraphicsScene, QGraphicsView, QGraphicsTextItem
from PySide6.QtCore import Qt
from PySide6.QtGui import QPainter
from talustrace.backend.models import TwistedPair
from talustrace.frontend.twisted_pair import TwistedPairItem
import sys

def main():
    app = QApplication(sys.argv)
    scene = QGraphicsScene(0, 0, 800, 600)
    view = QGraphicsView(scene)
    view.setWindowTitle("Twisted Pair Demo - Zoomed")
    view.setRenderHint(QPainter.Antialiasing)
    view.scale(3.0, 3.0)

    # Create model and item
    model = TwistedPair(
        id="demo_tp1",
        node_a=(100.0, 100.0),
        node_b=(400.0, 100.0),
        rotation_a=0,
        wire_id_1=None,
        wire_id_2=None,
        elbows=[]
    )
    item = TwistedPairItem(model)
    scene.addItem(item)

    # Add instructions
    instructions = QGraphicsTextItem(
        "Double-click wire to add elbow. Drag to move. Right-click elbow to delete. Drag anchors to move. Right-click anchor to Rotate."
    )
    instructions.setPos(20, 20)
    scene.addItem(instructions)

    # Simulate signals/colors
    pin_a0 = item.anchor_a.pins[0]
    pin_a1 = item.anchor_a.pins[1]
    item.set_signal(pin_a0, "wire_red", "red")
    item.set_signal(pin_a1, "wire_blue", "blue")

    view.setGeometry(100, 100, 820, 640)
    view.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
