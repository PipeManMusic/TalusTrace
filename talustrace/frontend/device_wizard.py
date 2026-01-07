import sys
import yaml
from pathlib import Path
from PySide6.QtWidgets import (
    QWizard, QWizardPage, QVBoxLayout, QLabel, QPushButton, QFileDialog,
    QLineEdit, QFormLayout, QGraphicsView, QGraphicsScene, QGraphicsItem,
    QGraphicsLineItem, QGraphicsEllipseItem, QTableWidget, QTableWidgetItem,
    QHeaderView, QHBoxLayout, QMessageBox, QGraphicsPixmapItem
)
from PySide6.QtSvgWidgets import QGraphicsSvgItem
from PySide6.QtCore import Qt, Signal, QPointF, QRectF
from PySide6.QtGui import QPen, QColor, QPainter, QPolygonF

class WizardCanvas(QGraphicsView):
    """Shared canvas for Scale and Pin pages."""
    click_signal = Signal(QPointF)
    drag_signal = Signal(QPointF, QPointF) # start, current

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.NoDrag)
        self._start_pos = None

    def set_svg(self, svg_path):
        self.scene.clear()
        self.svg_item = QGraphicsSvgItem(svg_path)
        self.scene.addItem(self.svg_item)
        self.setSceneRect(self.svg_item.boundingRect())
        self.fitInView(self.svg_item, Qt.KeepAspectRatio)

    def mousePressEvent(self, event):
        self._start_pos = self.mapToScene(event.position().toPoint())
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._start_pos:
            curr = self.mapToScene(event.position().toPoint())
            self.drag_signal.emit(self._start_pos, curr)
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if self._start_pos:
            pos = self.mapToScene(event.position().toPoint())
            # If essentially a click (minimal drag)
            if (pos - self._start_pos).manhattanLength() < 2:
                self.click_signal.emit(pos)
            self._start_pos = None
        super().mouseReleaseEvent(event)

class LoadPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Import Graphics")
        self.setSubTitle("Select an SVG file for your connector/device.")
        layout = QVBoxLayout()
        
        self.btn_load = QPushButton("Browse SVG...")
        self.btn_load.clicked.connect(self.load_svg)
        self.lbl_path = QLabel("No file selected")
        
        layout.addWidget(self.btn_load)
        layout.addWidget(self.lbl_path)
        self.setLayout(layout)
        self.svg_path = None

    def load_svg(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open SVG", "", "SVG Files (*.svg)")
        if path:
            self.svg_path = path
            self.lbl_path.setText(path)
            self.completeChanged.emit()

    def isComplete(self):
        return bool(self.svg_path)

class ScalePage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Calibrate Scale")
        self.setSubTitle("Click and drag to draw a line of known length (e.g., connector width).")
        
        self.view = WizardCanvas()
        self.view.drag_signal.connect(self.update_line)
        self.view.click_signal.connect(self.reset_line) # Click clears line to restart
        
        self.inp_mm = QLineEdit()
        self.inp_mm.setPlaceholderText("Length in mm (e.g. 25.4)")
        self.inp_mm.textChanged.connect(self.completeChanged.emit)
        
        layout = QVBoxLayout()
        layout.addWidget(self.view)
        form = QFormLayout()
        form.addRow("Real World Length (mm):", self.inp_mm)
        layout.addLayout(form)
        self.setLayout(layout)
        
        self.ref_line = None
        self.line_item = None

    def initializePage(self):
        path = self.wizard().field("svg_path")
        if path:
            self.view.set_svg(path)

    def update_line(self, start, end):
        if not self.line_item:
            self.line_item = QGraphicsLineItem()
            self.line_item.setPen(QPen(Qt.red, 2))
            self.view.scene.addItem(self.line_item)
        self.line_item.setLine(start.x(), start.y(), end.x(), end.y())
        self.ref_line = (start, end)
        self.completeChanged.emit()

    def reset_line(self, pos):
        if self.line_item:
            self.view.scene.removeItem(self.line_item)
            self.line_item = None
            self.ref_line = None
            self.completeChanged.emit()

    def isComplete(self):
        try:
            dist = float(self.inp_mm.text())
            return self.ref_line is not None and dist > 0
        except ValueError:
            return False

    def get_px_per_mm(self):
        if not self.ref_line: return 1.0
        p1, p2 = self.ref_line
        import math
        line_len_px = math.hypot(p2.x() - p1.x(), p2.y() - p1.y())
        real_mm = float(self.inp_mm.text())
        return line_len_px / real_mm

class PinPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Place Pins")
        self.setSubTitle("Click on the image to add pins.")
        
        self.view = WizardCanvas()
        self.view.click_signal.connect(self.add_pin)
        
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Pin ID", "Color"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        layout = QHBoxLayout()
        layout.addWidget(self.view, stretch=2)
        layout.addWidget(self.table, stretch=1)
        self.setLayout(layout)
        
        self.pins = [] # List of (x, y, id, color)

    def initializePage(self):
        path = self.wizard().field("svg_path")
        self.view.set_svg(path)

    def add_pin(self, pos):
        idx = len(self.pins) + 1
        marker = QGraphicsEllipseItem(pos.x()-3, pos.y()-3, 6, 6)
        marker.setBrush(Qt.blue)
        marker.setPen(Qt.NoPen)
        self.view.scene.addItem(marker)
        
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setItem(row, 0, QTableWidgetItem(str(idx)))
        self.table.setItem(row, 1, QTableWidgetItem("Red")) # Default
        
        self.pins.append({"pos": pos, "item": marker})

    def get_pin_data(self):
        data = []
        for i in range(self.table.rowCount()):
            pid = self.table.item(i, 0).text()
            color = self.table.item(i, 1).text()
            pos = self.pins[i]["pos"]
            data.append({"id": pid, "color": color, "x": pos.x(), "y": pos.y()})
        return data

class MetaPage(QWizardPage):
    def __init__(self):
        super().__init__()
        self.setTitle("Device Metadata")
        
        self.inp_name = QLineEdit()
        self.inp_desc = QLineEdit()
        
        layout = QFormLayout()
        layout.addRow("Device Name:", self.inp_name)
        layout.addRow("Description:", self.inp_desc)
        self.setLayout(layout)

    def isComplete(self):
        return bool(self.inp_name.text())

class DeviceCreatorWizard(QWizard):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("New Device Wizard")
        self.resize(900, 700)
        
        self.page_load = LoadPage()
        self.page_scale = ScalePage()
        self.page_pins = PinPage()
        self.page_meta = MetaPage()
        
        self.addPage(self.page_load)
        self.addPage(self.page_scale)
        self.addPage(self.page_pins)
        self.addPage(self.page_meta)
        
        # Register fields for data sharing
        self.page_load.registerField("svg_path", self.page_load.lbl_path, "text")

    def accept(self):
        # Gather Data
        svg_path = self.page_load.svg_path
        px_per_mm = self.page_scale.get_px_per_mm()
        pins = self.page_pins.get_pin_data()
        name = self.page_meta.inp_name.text()
        
        # Build Device Def (YAML content)
        device_def = {
            "name": name,
            "svg": svg_path,
            "scale_px_per_mm": px_per_mm,
            "pins": pins
        }
        
        # Save to library (Mock for now, just print or save local)
        # In the future, this will save to `library/devices/`
        print("--- Generated Device Definition ---")
        print(yaml.dump(device_def))
        print("-----------------------------------")
        
        QMessageBox.information(self, "Success", f"Device '{name}' definition generated (check console).")
        super().accept()