import os
import sys
from pathlib import Path
from PySide6.QtCore import QUrl, QTimer
from PySide6.QtGui import QFont, QFontDatabase, QIcon
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle
from PySide6.QtWidgets import QApplication, QMessageBox
from qml_backend import ShelfBackend
import preferences

APP_VERSION = "2.0.0"
RESOURCE_DIR = Path(__file__).resolve().parent
FONT_DIR = RESOURCE_DIR / "assets" / "fonts" / "medeo"

def load_ui_font():
    for name in ("MedeoSans-Regular.ttf", "MedeoSans-Medium.ttf", "MedeoSans-SemiBold.ttf", "MedeoSans-Bold.ttf"):
        font_id = QFontDatabase.addApplicationFont(str(FONT_DIR / name))
        if font_id < 0 or "Medeo Sans" not in QFontDatabase.applicationFontFamilies(font_id):
            return None
    return "Medeo Sans"

def create_engine(backend):
    engine = QQmlApplicationEngine()
    engine.load_errors = []
    messages = engine.load_errors
    engine.warnings.connect(lambda errors: messages.extend(error.toString() for error in errors))
    engine.rootContext().setContextProperty("shelf", backend)
    engine.load(QUrl.fromLocalFile(str(RESOURCE_DIR / "qml" / "Main.qml")))
    return engine

def main():
    os.environ.setdefault("QML_DISABLE_DISK_CACHE", "1")
    try:
        settings = preferences.load()
    except ValueError:
        settings = preferences.DEFAULTS
    os.environ["QT_SCALE_FACTOR"] = str(settings["ui_scale"])
    app = QApplication(sys.argv)
    app.setApplicationName("MovieShelf")
    app.setOrganizationName("MovieShelf")
    app.setApplicationVersion(APP_VERSION)
    app.setWindowIcon(QIcon(str(RESOURCE_DIR / "assets" / "icon.ico")))
    QQuickStyle.setStyle("Basic")
    family = load_ui_font()
    if settings["font_family"] in QFontDatabase.families():
        family = settings["font_family"]
    if family is None:
        families = QFontDatabase.families()
        family = next((name for name in ("Segoe UI Variable", "Segoe UI", "Noto Sans") if name in families), app.font().family())
    font = QFont(family)
    font.setPixelSize(round(14 * settings["text_scale"]))
    app.setFont(font)
    backend = ShelfBackend()
    engine = create_engine(backend)
    if not engine.rootObjects():
        QMessageBox.critical(None, "MovieShelf", "The interface could not be loaded.\n\n" + "\n".join(engine.load_errors))
        del engine
        return 1
    if backend.startup_errors:
        QTimer.singleShot(100, lambda: backend.errorOccurred.emit("\n\n".join(backend.startup_errors)))
    result = app.exec()
    del engine
    return result

if __name__ == "__main__":
    sys.exit(main())
