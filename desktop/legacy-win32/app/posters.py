from functools import lru_cache
from pathlib import Path
from PySide2.QtCore import Qt, QRectF, QSize, Signal
from PySide2.QtGui import QColor, QImageReader, QPainter, QPainterPath, QPixmap
from PySide2.QtWidgets import QWidget
from i18n import t

@lru_cache(maxsize=12)
def _read_image(filename, modified):
    reader = QImageReader(filename)
    reader.setAutoTransform(True)
    size = reader.size()
    if size.width() > 2048 or size.height() > 2048:
        size.scale(QSize(2048, 2048), Qt.KeepAspectRatio)
        reader.setScaledSize(size)
    return QPixmap.fromImage(reader.read())

@lru_cache(maxsize=16)
def _scaled_image(filename, modified, width, height):
    original = _read_image(filename, modified)
    return QPixmap.fromImage(original.toImage().scaled(
        width, height, Qt.IgnoreAspectRatio,
        Qt.SmoothTransformation))

class PosterView(QWidget):
    changed = Signal()
    clicked = Signal()
    imageDropped = Signal(str)

    def __init__(self, path=None, crop=None, editable=False, parent=None):
        super().__init__(parent)
        self.editable = editable
        self.pixmap = QPixmap()
        self.crop = {"zoom": 1.0, "x": 0.0, "y": 0.0, "mode": "fill"}
        self.drag_start = None
        self.drag_active = False
        self.setAcceptDrops(editable)
        self.set_image(path, crop)
        self.setCursor(Qt.OpenHandCursor if editable else Qt.PointingHandCursor)

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
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setRenderHint(QPainter.SmoothPixmapTransform)
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
            painter.drawText(self.rect(), Qt.AlignCenter,
                             t("Drop an image here") if self.drag_active else t("NO ARTWORK\nAdd your own poster"))
        if self.drag_active and not self.pixmap.isNull():
            painter.fillRect(self.rect(), QColor(0, 122, 255, 80))
            painter.setPen(QColor("#ffffff"))
            painter.drawText(self.rect(), Qt.AlignCenter, t("Drop an image here"))

    def _drop_path(self, event):
        if not self.editable or not event.mimeData().hasUrls():
            return None
        for url in event.mimeData().urls():
            path = url.toLocalFile()
            if path and QImageReader(path).canRead():
                return path
        return None

    def dragEnterEvent(self, event):
        if self._drop_path(event):
            self.drag_active = True
            event.acceptProposedAction()
            self.update()

    def dragMoveEvent(self, event):
        if self._drop_path(event):
            event.acceptProposedAction()

    def dragLeaveEvent(self, event):
        self.drag_active = False
        self.update()

    def dropEvent(self, event):
        path = self._drop_path(event)
        self.drag_active = False
        self.update()
        if path:
            self.imageDropped.emit(path)
            event.acceptProposedAction()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.editable:
                self.drag_start = event.pos()
                self.start_crop = dict(self.crop)
                self.setCursor(Qt.ClosedHandCursor)
            else:
                self.clicked.emit()

    def mouseMoveEvent(self, event):
        if self.drag_start is None or not self.editable:
            return
        delta = event.pos() - self.drag_start
        rect = self.image_rect()
        for axis, distance, overflow in (("x", delta.x(), abs(rect.width()-self.width())), ("y", delta.y(), abs(rect.height()-self.height()))):
            if overflow > 1:
                self.crop[axis] = max(-1, min(1, self.start_crop[axis] + distance*2/overflow))
        self.update()
        self.changed.emit()

    def mouseReleaseEvent(self, event):
        self.drag_start = None
        if self.editable:
            self.setCursor(Qt.OpenHandCursor)
