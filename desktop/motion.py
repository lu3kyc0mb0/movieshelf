from PySide6.QtCore import QEasingCurve, QPropertyAnimation
from PySide6.QtWidgets import QGraphicsOpacityEffect
import preferences


def fade_in(widget):
    if not preferences.load()["animations"]:
        return
    effect = widget.graphicsEffect()
    if not isinstance(effect, QGraphicsOpacityEffect):
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)
    previous = getattr(widget, "_fade", None)
    if previous:
        previous.stop()
        previous.deleteLater()
    animation = QPropertyAnimation(effect, b"opacity", widget)
    animation.setDuration(220)
    animation.setStartValue(0.35)
    animation.setEndValue(1.0)
    animation.setEasingCurve(QEasingCurve.Type.OutCubic)
    widget._fade = animation
    animation.start()
