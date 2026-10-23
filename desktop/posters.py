from functools import lru_cache
from pathlib import Path
from PySide6.QtCore import Qt, QRectF, QSize, Signal
from PySide6.QtGui import QColor, QImageReader, QPainter, QPainterPath, QPixmap
from PySide6.QtWidgets import QWidget

@lru_cache(maxsize=12)
def _read_image(filename, modified):
    reader = QImageReader(filename)
    reader.setAutoTransform(True)
    size = reader.size()
    if size.width() > 2048 or size.height() > 2048:
        size.scale(QSize(2048, 2048), Qt.AspectRatioMode.KeepAspectRatio)
        reader.setScaledSize(size)
    return QPixmap.fromImage(reader.read())

@lru_cache(maxsize=16)
def _scaled_image(filename, modified, width, height):
    original = _read_image(filename, modified)
    return QPixmap.fromImage(original.toImage().scaled(
        width, height, Qt.AspectRatioMode.IgnoreAspectRatio,
        Qt.TransformationMode.SmoothTransformation))

class PosterView(QWidget):
    changed = Signal()
    clicked = Signal()

    def __init__(self, path=None, crop=None, editable=False, parent=None):
        super().__init__(parent)
        self.editable = editable
        self.pixmap = QPixmap()
        self.crop = {"zoom": 1.0, "x": 0.0, "y": 0.0, "mode": "fill"}
        self.drag_start = None
        self.set_image(path, crop)
        self.setCursor(Qt.CursorShape.OpenHandCursor if editable else Qt.CursorShape.PointingHandCursor)

    def set_image(self, path, crop=None):
        self.pixmap = QPixmap()
        self.source = None
        if path:
            path = Path(path)
            try:
                if path.is_file():
                    self.source = (str(path), path.stat().st_mtime_ns)
                    self.pixmap = _read_image(*self.source)
            except OSError:
                self.source = None
        if crop is not None:
            self.crop.update(crop)
        self.update()

    def image_rect(self):
        if self.pixmap.isNull():
            return QRectF()
        w, h = self.width(), self.height()
        sizes = w / self.pixmap.width(), h / self.pixmap.height()
        scale = (min(sizes) if self.crop["mode"] == "fit" else max(sizes)) * self.crop["zoom"]
        iw, ih = self.pixmap.width() * scale, self.pixmap.height() * scale
        return QRectF((w-iw)/2 + self.crop["x"]*abs(w-iw)/2,
                      (h-ih)/2 + self.crop["y"]*abs(h-ih)/2, iw, ih)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform)
        clip = QPainterPath()
        clip.addRoundedRect(QRectF(self.rect()), 10, 10)
        painter.setClipPath(clip)
        painter.fillRect(self.rect(), self.palette().alternateBase())
        if not self.pixmap.isNull():
            rect = self.image_rect()
            dpr = self.devicePixelRatioF()
            width, height = max(1, round(rect.width()*dpr)), max(1, round(rect.height()*dpr))
            limit = min(1, 2048/max(width, height))
            scaled = _scaled_image(*self.source, max(1, round(width*limit)), max(1, round(height*limit)))
            painter.drawPixmap(rect, scaled, QRectF(scaled.rect()))
        else:
            painter.setPen(QColor("#979da9"))
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "NO ARTWORK\nAdd your own poster")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.editable:
                self.drag_start = event.position()
                self.start_crop = dict(self.crop)
                self.setCursor(Qt.CursorShape.ClosedHandCursor)
            else:
                self.clicked.emit()

    def mouseMoveEvent(self, event):
        if self.drag_start is None or not self.editable:
            return
        delta = event.position() - self.drag_start
        rect = self.image_rect()
        for axis, distance, overflow in (("x", delta.x(), abs(rect.width()-self.width())), ("y", delta.y(), abs(rect.height()-self.height()))):
            if overflow > 1:
                self.crop[axis] = max(-1, min(1, self.start_crop[axis] + distance*2/overflow))
        self.update()
        self.changed.emit()

    def mouseReleaseEvent(self, event):
        self.drag_start = None
        if self.editable:
            self.setCursor(Qt.CursorShape.OpenHandCursor)
