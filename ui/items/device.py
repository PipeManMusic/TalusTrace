"""
DeviceItem: QGraphicsRectItem subclass for representing devices in the scene.
Handles device geometry, style, and pin placement.
"""
from PySide6.QtWidgets import QGraphicsItem, QGraphicsRectItem
from PySide6.QtGui import QPen, QBrush, QColor, QPixmap, QPainter
from PySide6.QtCore import Qt, QByteArray, QRectF

try:
    from PySide6.QtSvg import QSvgRenderer
except ImportError:
    QSvgRenderer = None

from ui.coordinates import THEME_FALLBACK
from ui.items.base import SelectableItemMixin
from ui.items.observable_graphics_item_mixin import ObservableGraphicsItemMixin
from ui.items.pin import PinItem

class DeviceItem(ObservableGraphicsItemMixin, SelectableItemMixin, QGraphicsRectItem):
    """
    QGraphicsRectItem subclass for device visualization and interaction.
    Handles device geometry, style, and pin placement in the scene.
    """
    __test_scenario__ = {
        'model_data': {'meta': {'width_mm': 40.0, 'height_mm': 30.0}, 'x': 0, 'y': 0, 'rotation': 0.0, 'pins': []},
        'expected_child_count': 0
    }

    # Maximum size (px per side) of the cached SVG rasterization.  Caps memory
    # use when zoomed in while keeping the artwork sharp at typical zoom levels.
    _SVG_CACHE_MAX_PX = 2048
    
    def __init__(self, device, is_ghost=False, parent=None):
        """
        Initialize the DeviceItem.
        Args:
            device: The device model object.
            is_ghost (bool): Whether this is a ghost (preview) item.
            parent: Optional parent QGraphicsItem.
        """
        from infra.logging import infra_log
        QGraphicsRectItem.__init__(self, parent)
        ObservableGraphicsItemMixin.__init__(self)
        infra_log(f"[DeviceItem] Created DeviceItem for model id={getattr(device, 'id', None)}, obj={device}, DeviceItem id={id(self)}", level="debug")
        self.setZValue(10)  # Devices above wires
        # NoCache: DeviceCoordinateCache renders the item into an offscreen
        # pixmap sized in *device* pixels, which grows without bound as you
        # zoom in and exhausts memory.  Devices are simple shapes / vector SVGs
        # that render cheaply and sharply at any zoom, so no cache is needed.
        self.setCacheMode(QGraphicsItem.NoCache)

        self._svg_renderer = None
        # Bounded self-managed rasterization of the SVG.  The device uses
        # NoCache (Qt's DeviceCoordinateCache grows without bound when zooming
        # in), so without this every repaint — including the one triggered by
        # selecting the device — re-rasterizes the entire (potentially very
        # complex) SVG.  We cache a QPixmap sized to the on-screen device size,
        # capped at _SVG_CACHE_MAX_PX per side, and reuse it while the on-screen
        # size is unchanged (selection, hover, pan).  It is re-rendered only
        # when the zoom level changes materially.
        self._svg_pixmap = None
        self._svg_pixmap_key = None

        # ARCHITECTURE UPDATE: Use MM dimensions directly
        width_mm = device.meta.get("width_mm", 40.0)
        height_mm = device.meta.get("height_mm", 30.0)

        self._apply_grid_rect(width_mm, height_mm)

        # No conversion needed. Model x/y is MM. Scene is MM.
        self.setPos(device.x, device.y)

        rotation = getattr(device, 'rotation', 0.0)
        self.setRotation(rotation)

        self.init_mixin(device, is_ghost)

        # Honour the model's visibility flag (project-browser show/hide).
        self.setVisible(getattr(device, 'visible', True))
        
        # Load SVG if present
        self._load_svg()

        if not self.is_ghost and hasattr(device, 'pins'):
            # NOTE: Registration of scene items is handled by Canvas/LayoutManager after item creation
            # The Item does NOT register itself - separation of concerns
            for pin in device.pins:
                pin_item = PinItem(pin, self)
                # Pin positions in model are relative MM. Use directly.
                pin_item.setPos(pin.x, pin.y)
                # Ensure PinItem is added to the scene as a child of DeviceItem
                if self.scene() is not None:
                    self.scene().addItem(pin_item)

    def _load_svg(self):
        """Internal helper to load SVG data from the model into the renderer."""
        # Invalidate any cached rasterization; the source artwork may have changed.
        self._svg_pixmap = None
        self._svg_pixmap_key = None
        svg_body = getattr(self.model, 'svg_body', None)
        if svg_body and QSvgRenderer is not None:
            if not self._svg_renderer:
                self._svg_renderer = QSvgRenderer()
            # QSvgRenderer.load expects bytes
            self._svg_renderer.load(QByteArray(svg_body.encode('utf-8')))
            if not self._svg_renderer.isValid():
                self._svg_renderer = None
            else:
                # Vector SVGs render sharply at any zoom; caching to a device
                # pixmap would balloon in memory when zoomed in.
                self.setCacheMode(QGraphicsItem.NoCache)
        else:
            self._svg_renderer = None

    def update_from_model(self):
        """
        Update the item's position, size, and visuals to match the model, including meta fields.
        """
        # Update position
        self.setPos(self.model.x, self.model.y)
        # Update size and origin from meta fields
        width_mm = self.model.meta.get("width_mm", 40.0)
        height_mm = self.model.meta.get("height_mm", 30.0)
        self._apply_grid_rect(width_mm, height_mm)
        self.setRotation(getattr(self.model, 'rotation', 0.0))
        
        # Re-parse the SVG in case it was updated in the library/model
        self._load_svg()
        self._apply_style()
        self.setVisible(getattr(self.model, 'visible', True))
        self.update()  # Force redraw in case of visual artifacts

    def _apply_grid_rect(self, width_mm, height_mm):
        """Set the device rect offset so grid lines are centered in the body.

        The local origin (0, 0) stays on-grid.  The visible rectangle is
        shifted left/up by half the remainder so that grid columns/rows
        are evenly distributed across the device body.
        """
        grid = 2.54
        try:
            from api.manager import APIManager
            grid = APIManager.get_instance().settings.grid_size_mm
        except Exception:
            pass
        margin_x = (width_mm % grid) / 2.0
        margin_y = (height_mm % grid) / 2.0
        self.setRect(-margin_x, -margin_y, width_mm, height_mm)
        self.setTransformOriginPoint(-margin_x + width_mm / 2.0,
                                     -margin_y + height_mm / 2.0)

    @property
    def device(self):
        """
        Get the device model associated with this item.
        Returns:
            The device model object.
        """
        return self.model

    @device.setter
    def device(self, value):
        """
        Set the device model for this item.
        Args:
            value: The new device model object.
        """
        self.model = value

    def boundingRect(self):
        """
        Return the bounding rectangle, adjusted for selection halo.
        Returns:
            QRectF: The adjusted bounding rectangle.
        """
        return super().boundingRect().adjusted(-2, -2, 2, 2)

    def _apply_style(self):
        """
        Apply the visual style (pen and brush) to the device item.
        """
        body_color = QColor(THEME_FALLBACK["device_body"])
        outline_color = QColor(THEME_FALLBACK["device_outline"])
        
        # Cosmetic Pen (Width 0) ensures it draws nicely at any zoom level
        pen_style = Qt.DashLine if self.is_ghost else Qt.SolidLine
        pen = QPen(outline_color, 0, pen_style)
        pen.setCosmetic(True)

        if self.is_ghost:
            body_color.setAlpha(100)

        # Only apply the fallback brush if we don't have an SVG
        if self._svg_renderer:
            self.setBrush(Qt.NoBrush)
            self.setPen(Qt.NoPen)
        else:
            self.setPen(pen)
            self.setBrush(QBrush(body_color))

    def _svg_target_rect(self):
        """Return the rect to render the SVG into, preserving its aspect ratio.

        ``QSvgRenderer.render(painter, bounds)`` stretches the SVG's viewBox to
        exactly fill ``bounds``, distorting the artwork when the device
        footprint (width_mm x height_mm) has a different aspect ratio than the
        SVG viewBox.  This computes the largest rect with the viewBox aspect
        that fits inside the device rect and centres it (letterbox), so the
        drawing is never squashed or stretched.
        """
        rect = self.rect()
        renderer = self._svg_renderer
        if renderer is None:
            return rect
        vb = renderer.viewBoxF()
        if vb.width() <= 0 or vb.height() <= 0 or rect.width() <= 0 or rect.height() <= 0:
            return rect
        svg_aspect = vb.width() / vb.height()
        rect_aspect = rect.width() / rect.height()
        if rect_aspect > svg_aspect:
            # Device rect is wider than the SVG: constrain by height.
            h = rect.height()
            w = h * svg_aspect
        else:
            # Device rect is taller/narrower: constrain by width.
            w = rect.width()
            h = w / svg_aspect
        x = rect.x() + (rect.width() - w) / 2.0
        y = rect.y() + (rect.height() - h) / 2.0
        return QRectF(x, y, w, h)

    def _paint_svg_cached(self, painter):
        """Draw the SVG via a bounded, zoom-aware pixmap cache.

        Rasterizes the SVG once per on-screen size into a QPixmap and reuses it
        across repaints (selection, hover, pan) instead of re-rendering the
        vector artwork every frame.  Falls back to direct vector rendering when
        rasterization is not worthwhile (tiny) or unavailable.
        """
        target = self._svg_target_rect()
        if target.width() <= 0 or target.height() <= 0:
            return

        # On-screen size of the target rect in device pixels.  Use the full
        # transform magnitude (not just m11) so rotated devices still rasterize
        # at the correct resolution.
        import math
        t = painter.worldTransform()
        sx = math.hypot(t.m11(), t.m12()) or 1.0
        sy = math.hypot(t.m21(), t.m22()) or 1.0
        dev_w = abs(target.width() * sx)
        dev_h = abs(target.height() * sy)
        if dev_w < 1 or dev_h < 1:
            return

        # Cap the raster size (bounds memory when zoomed in) and preserve aspect.
        max_px = self._SVG_CACHE_MAX_PX
        clamp = min(1.0, max_px / max(dev_w, dev_h))
        px_w = max(1, int(round(dev_w * clamp)))
        px_h = max(1, int(round(dev_h * clamp)))

        # Bucket the key so tiny sub-pixel changes don't thrash the cache.
        key = (px_w, px_h)
        if self._svg_pixmap is None or self._svg_pixmap_key != key:
            pixmap = QPixmap(px_w, px_h)
            pixmap.fill(Qt.transparent)
            p = QPainter(pixmap)
            p.setRenderHint(QPainter.Antialiasing, True)
            self._svg_renderer.render(p, QRectF(0, 0, px_w, px_h))
            p.end()
            self._svg_pixmap = pixmap
            self._svg_pixmap_key = key

        painter.setRenderHint(QPainter.SmoothPixmapTransform, True)
        painter.drawPixmap(target, self._svg_pixmap, QRectF(self._svg_pixmap.rect()))

    def paint(self, painter, option, widget):
        """
        Paint the device item, including SVG rendering and selection highlights.
        Args:
            painter: QPainter object.
            option: QStyleOptionGraphicsItem.
            widget: Optional widget being painted on.
        """
        # If we have SVG data, render it. Otherwise fall back to drawing the standard rect box
        if self._svg_renderer:
            if self.is_ghost:
                painter.setOpacity(0.5)
            self._paint_svg_cached(painter)
            if self.is_ghost:
                painter.setOpacity(1.0) # restore opacity
        else:
            super().paint(painter, option, widget)

        # Draw selection highlight
        if self.isSelected() and not self.is_ghost:
            from ui.coordinates import THEME_FALLBACK
            rect = self.rect().adjusted(-1, -1, 1, 1)
            highlight = QColor(THEME_FALLBACK["selection_highlight"])
            highlight.setAlpha(150)
            pen = QPen(highlight, 0, Qt.SolidLine)
            pen.setCosmetic(True)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawRect(rect)