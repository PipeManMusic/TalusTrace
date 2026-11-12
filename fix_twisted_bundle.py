import re
from pathlib import Path

path = Path("talustrace/frontend/items_baseline.py")
content = path.read_text(encoding="utf-8")

# 1. Fix the Syntax Error (unescape quotes from previous bad write)
# This fixes the "SyntaxError: unexpected character..." issue
content = content.replace(r'\"\"\"', '"""')

# 2. Add QVector2D Import if missing
if "QVector2D" not in content:
    content = content.replace(
        "from PySide6.QtGui import QPen, QBrush, QColor, QFont, QAction, QPainterPath, QPainterPathStroker, QPainter",
        "from PySide6.QtGui import QPen, QBrush, QColor, QFont, QAction, QPainterPath, QPainterPathStroker, QPainter, QVector2D"
    )

# 3. Define the New Simplified Class
new_class = '''class TwistedBundleItem(QGraphicsPathItem):
    """Simplified Twisted Pair connector (Bezier 'Eye' shape).
    Connects two TwistNodeItems with a clean, dynamic bulge pattern.
    """

    def __init__(self, source_node: TwistNodeItem, target_node: TwistNodeItem, on_changed=None):
        super().__init__()
        self.source_node = source_node
        self.target_node = target_node
        self.on_changed = on_changed

        self.color_a = QColor(255, 80, 80)
        self.color_b = QColor(80, 180, 255)

        self.path_a = QPainterPath()
        self.path_b = QPainterPath()

        self.halo_path = QGraphicsPathItem(self)
        self.halo_path.setPen(QPen(SELECTED_COLOR, 8))
        self.halo_path.setOpacity(0.45)
        self.halo_path.hide()
        self.halo_path.setZValue(-1)

        self.setFlags(QGraphicsItem.ItemIsSelectable)
        self.setZValue(-0.8)

        self.update_geometry()

    def update_geometry(self):
        # 1. Get positions
        start = self.source_node.get_pin_tip_scene_pos("H")
        end = self.target_node.get_pin_tip_scene_pos("L")
        
        # 2. Vector Math
        diff = QVector2D(end - start)
        length = diff.length()
        if length < 1:
            # If too close, just clear path
            self.setPath(QPainterPath())
            return

        diff.normalize()
        # Normal vector (-y, x)
        normal = QVector2D(-diff.y(), diff.x())
        
        # 3. Control Points for 'Eye' Shape
        spread = 15.0
        if length < 50: spread = length * 0.3 # Scale down for short wires

        p1_base = start + (diff.toPointF() * (length * 0.33))
        p2_base = start + (diff.toPointF() * (length * 0.66))
        
        offset = normal.toPointF() * spread

        # Wire A (Upper/Right bulge)
        self.path_a = QPainterPath(start)
        self.path_a.cubicTo(p1_base + offset, p2_base + offset, end)

        # Wire B (Lower/Left bulge)
        self.path_b = QPainterPath(start)
        self.path_b.cubicTo(p1_base - offset, p2_base - offset, end)

        # 4. Set Hit Area (Envelope)
        env = QPainterPath(start)
        env.addPath(self.path_a)
        env.addPath(self.path_b)
        self.setPath(env)
        self.halo_path.setPath(env)
        
        self._update_colors_from_nodes()
        if callable(self.on_changed):
            self.on_changed()

    def _update_colors_from_nodes(self):
        c_high = self.source_node.first_wire_color("H") or self.target_node.first_wire_color("H")
        c_low = self.source_node.first_wire_color("L") or self.target_node.first_wire_color("L")
        if c_high:
            self.color_a = c_high
        if c_low:
            self.color_b = c_low

    def paint(self, painter, option, widget=None):
        pen_a = QPen(self.color_a, 3)
        pen_b = QPen(self.color_b, 3)
        pen_a.setCapStyle(Qt.RoundCap)
        pen_b.setCapStyle(Qt.RoundCap)
        painter.setRenderHint(QPainter.Antialiasing, True)
        
        painter.setPen(pen_a)
        painter.drawPath(self.path_a)
        
        painter.setPen(pen_b)
        painter.drawPath(self.path_b)

    def shape(self):
        stroker = QPainterPathStroker()
        stroker.setWidth(14)
        return stroker.createStroke(self.path())

    def itemChange(self, change, value):
        if change == QGraphicsItem.ItemSelectedHasChanged:
            self.halo_path.setVisible(value)
        return super().itemChange(change, value)
'''

# 4. Replace the old class
# Use regex to find "class TwistedBundleItem..." and replace everything following it.
pattern = re.compile(r'class TwistedBundleItem.*', re.DOTALL)

if pattern.search(content):
    content = pattern.sub(new_class, content)
    print("Found existing TwistedBundleItem class and replaced it.")
else:
    # If regex fails (maybe due to corruption), append to end
    print("TwistedBundleItem class not found. Appending new class to end of file.")
    content += "\n\n" + new_class

path.write_text(content, encoding="utf-8")
print("✅ Success: items_baseline.py has been repaired and updated.")