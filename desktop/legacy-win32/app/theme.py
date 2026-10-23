import re
from PySide2.QtGui import QColor, QFont, QFontDatabase, QPalette
import preferences

STYLE = """
QWidget { color: #202126; font-size: 13px; }
QMainWindow, QDialog { background: #fafafa; }
QLabel { background: transparent; }
QFrame#sidebar { background: #eeeff2; border-right: 1px solid #e1e2e6; }
QLabel#brand { font-size: 23px; font-weight: 700; letter-spacing: -1px; }
QLabel#eyebrow { color: #8a8d96; font-size: 10px; font-weight: 700; letter-spacing: 2px; }
QLabel#title { font-size: 34px; font-weight: 700; letter-spacing: -1px; }
QLabel#subtitle { color: #858892; }
QLabel#section { font-size: 17px; font-weight: 650; }
QLabel#metric { font-size: 25px; font-weight: 650; }
QLabel#rating { color: #a46a08; font-weight: 650; }
QFrame#stat { background: #ffffff; border: 1px solid #e7e8eb; border-radius: 14px; }
QFrame#card { background: #ffffff; border: 1px solid #e8e9ec; border-radius: 14px; }
QFrame#card:hover { border: 1px solid #b6cef7; background: #fdfefe; }
QPushButton { background: #ededf0; border: none; border-radius: 8px; padding: 9px 15px; font-weight: 600; }
QPushButton:hover { background: #e1e3e9; }
QPushButton:disabled { color: #a1a4ad; background: #eeeff2; }
QPushButton#primary { background: #007aff; color: white; }
QPushButton#primary:hover { background: #0069df; }
QPushButton#danger { color: #dc3c37; background: #fff0ef; }
QPushButton#nav { text-align: left; padding: 11px 14px; background: transparent; color: #595d66; }
QPushButton#nav:hover { background: #e3e5eb; }
QPushButton#nav:checked { color: #006adf; background: #dce8fa; }
QLineEdit, QTextEdit, QSpinBox, QComboBox {
 background: white; border: 1px solid #dcdfe5; border-radius: 8px; padding: 8px 10px;
 selection-background-color: #d9e9ff; selection-color: #202126; }
QLineEdit:focus, QTextEdit:focus, QSpinBox:focus { border: 1px solid #007aff; }
QComboBox::drop-down { border: 0; width: 24px; }
QComboBox QAbstractItemView { background: white; selection-background-color: #dce8fa; color: #202126; }
QTabWidget::pane { border: none; background: transparent; }
QTabBar::tab { background: #eeeff2; padding: 9px 20px; margin: 3px; border-radius: 7px; color: #717580; }
QTabBar::tab:selected { background: #ffffff; color: #007aff; }
QSlider::groove:horizontal { height: 4px; background: #e0e3e9; border-radius: 2px; }
QSlider::sub-page:horizontal { background: #007aff; border-radius: 2px; }
QSlider::handle:horizontal { background: white; border: 1px solid #c8ccd4; width: 16px; margin: -6px 0; border-radius: 8px; }
QScrollArea { background: transparent; border: none; }
QScrollBar:vertical { background: transparent; width: 8px; }
QScrollBar::handle:vertical { background: #c8cbd2; border-radius: 4px; min-height: 30px; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
QStatusBar { background: #fafafa; color: #858892; }
QCheckBox { spacing: 8px; padding: 6px 0; }
QToolTip { background: #ffffff; color: #333740; border: 1px solid #dcdfe5; padding: 5px; }
"""

def apply_theme(app, mode=None):
    dark = (mode or preferences.DEFAULTS["theme"]) == "dark"
    families = QFontDatabase().families()
    family = next((name for name in ("SF Pro Text", ".AppleSystemUIFont", "Segoe UI Variable", "Segoe UI", "Arial") if name in families), app.font().family())
    app.setFont(QFont(family, 10))
    app.setStyle("Fusion")
    palette = QPalette()
    for role, color in ((QPalette.Window, "#fafafa"),
                        (QPalette.Base, "#ffffff"),
                        (QPalette.Button, "#ededf0"),
                        (QPalette.Text, "#202126"),
                        (QPalette.WindowText, "#202126"),
                        (QPalette.ButtonText, "#202126"),
                        (QPalette.Highlight, "#007aff"),
                        (QPalette.HighlightedText, "#ffffff")):
        palette.setColor(role, QColor(color))
    app.setPalette(palette)
    colors = {
        "#fafafa": "#17181c", "#ffffff": "#24262c", "white": "#24262c",
        "#202126": "#eceef3", "#eeeff2": "#202126", "#e1e2e6": "#30323b",
        "#8a8d96": "#9296a3", "#858892": "#a2a7b5", "#a46a08": "#e8b965",
        "#e7e8eb": "#33353f", "#e8e9ec": "#353741", "#b6cef7": "#527cac",
        "#fdfefe": "#2b2e36", "#ededf0": "#31343d", "#e1e3e9": "#3d414c",
        "#fff0ef": "#3a252b", "#dc3c37": "#ff8c86", "#595d66": "#b7bdc9",
        "#e3e5eb": "#30343e", "#006adf": "#7db6ff", "#dce8fa": "#253c5a",
        "#dcdfe5": "#414550", "#d9e9ff": "#335a88", "#717580": "#b5bac7",
        "#e0e3e9": "#414550", "#c8ccd4": "#6b7283", "#c8cbd2": "#555d6c",
        "#333740": "#eceef3",
    }
    if dark:
        for role, color in ((QPalette.Window, "#17181c"),
                            (QPalette.Base, "#24262c"),
                            (QPalette.Button, "#31343d"),
                            (QPalette.Text, "#eceef3"),
                            (QPalette.WindowText, "#eceef3"),
                            (QPalette.ButtonText, "#eceef3")):
            palette.setColor(role, QColor(color))
    palette.setColor(QPalette.AlternateBase, QColor("#30343f" if dark else "#e9eaf0"))
    app.setPalette(palette)
    style = re.sub(r"#[0-9a-fA-F]{6}|\bwhite\b", lambda m: colors.get(m[0], m[0]), STYLE) if dark else STYLE
    style += "\nQPushButton#primary { color: #ffffff; } QLineEdit#bigSearch { font-size: 24px; padding: 17px; }"
    app.setStyleSheet(style)
