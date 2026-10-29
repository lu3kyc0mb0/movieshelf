from PySide6.QtCore import Qt
from PySide6.QtGui import QKeySequence

ACTIONS = [
    {"id": "new_movie", "title": "Add movie manually", "group": "Library", "default": "Ctrl+N"},
    {"id": "tmdb", "title": "Find a movie on TMDB", "group": "Library", "default": "Ctrl+Shift+N"},
    {"id": "search", "title": "Search", "group": "Library", "default": "Ctrl+F"},
    {"id": "library", "title": "Library", "group": "Navigation", "default": "Alt+1"},
    {"id": "watchlist", "title": "Watchlist", "group": "Navigation", "default": "Alt+2"},
    {"id": "watched", "title": "Watched", "group": "Navigation", "default": "Alt+3"},
    {"id": "favorites", "title": "Favorites", "group": "Navigation", "default": "Alt+4"},
    {"id": "settings", "title": "Settings", "group": "Tools", "default": "Ctrl+,"},
    {"id": "insights", "title": "Collection insights", "group": "Tools", "default": "Ctrl+I"},
    {"id": "collections", "title": "Manage collections", "group": "Tools", "default": "Ctrl+Shift+C"},
    {"id": "save", "title": "Save movie", "group": "Editor", "default": "Ctrl+S"},
]
DEFAULTS = {action["id"]: action["default"] for action in ACTIONS}
RESERVED = {"Ctrl+A", "Ctrl+C", "Ctrl+V", "Ctrl+X", "Ctrl+Z", "Ctrl+Y", "Ctrl+Shift+Z", "Ctrl+Tab", "Ctrl+Shift+Tab", "Alt+F4", "Meta+Q", "Meta+C", "Meta+V", "Meta+X", "Meta+A", "Meta+Z"}

def normalize(value):
    if not isinstance(value, str) or len(value) > 80:
        raise ValueError("Invalid keyboard shortcut.")
    if not value.strip():
        return ""
    sequence = QKeySequence.fromString(value, QKeySequence.SequenceFormat.PortableText)
    if sequence.count() != 1:
        raise ValueError("Use one key combination per action.")
    key = sequence[0].key()
    modifiers = sequence[0].keyboardModifiers()
    if key in (Qt.Key.Key_unknown, Qt.Key.Key_Escape, Qt.Key.Key_Tab, Qt.Key.Key_Backtab, Qt.Key.Key_Return, Qt.Key.Key_Enter, Qt.Key.Key_Control, Qt.Key.Key_Shift, Qt.Key.Key_Alt, Qt.Key.Key_Meta):
        raise ValueError("This key is reserved for keyboard navigation.")
    if not modifiers & (Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.AltModifier | Qt.KeyboardModifier.MetaModifier) and not Qt.Key.Key_F1 <= key <= Qt.Key.Key_F35:
        raise ValueError("Use Ctrl, Alt, Command or a function key.")
    result = sequence.toString(QKeySequence.SequenceFormat.PortableText)
    if result in RESERVED:
        raise ValueError("This shortcut is reserved for text editing or the operating system.")
    return result

def validate(values):
    if not isinstance(values, dict) or set(values) - set(DEFAULTS):
        raise ValueError("Invalid keyboard shortcuts.")
    result = dict(DEFAULTS)
    result.update(values)
    used = set()
    for key, value in result.items():
        result[key] = normalize(value)
        if result[key] and result[key] in used:
            raise ValueError("Two actions use the same shortcut.")
        used.add(result[key])
    return result
