import os
import tempfile
from pathlib import Path
import zipfile
from PySide2.QtCore import Qt, QSize
from PySide2.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from PySide2.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDialog, QFileDialog, QFormLayout,
    QHBoxLayout, QInputDialog, QLabel, QLineEdit, QListWidget, QListWidgetItem, QMessageBox,
    QPushButton, QSlider, QVBoxLayout, QScrollArea, QWidget,
)
import movie_store as store
import preferences
from editor import label
from motion import fade_in
from posters import PosterView
from i18n import t

class MoviePreview(QDialog):
    def __init__(self, parent, movie):
        super().__init__(parent)
        self.setWindowTitle(t("Saved movie") + " · MovieShelf")
        self.resize(800, 600)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 24)
        body = QHBoxLayout()
        body.setSpacing(28)
        poster = PosterView(store.poster_path(movie), movie.get("poster_crop"))
        poster.setFixedSize(260, 390)
        body.addWidget(poster, alignment=Qt.AlignTop)
        content = QWidget()
        text = QVBoxLayout(content)
        title = label(movie["title"], "title")
        title.setWordWrap(True)
        text.addWidget(title)
        text.addWidget(label(f"{movie['year']}  ·  ID #{movie['id']}", "subtitle"))
        text.addWidget(label(f"{movie['rating']}/10" if movie.get("rating") else t("Not rated"), "rating"))
        text.addWidget(label(t("Watched" if movie.get("status") == "watched" else "Want to watch"), "subtitle"))
        names = {item["id"]: item["name"] for item in getattr(parent, "collections", [])}
        for caption, values in (("Genres", movie.get("genres", [])), ("Tags", movie.get("tags", [])),
                                ("Collections", [names[item] for item in movie.get("collections", []) if item in names])):
            if values:
                text.addWidget(label(f"{t(caption)}: {', '.join(values)}", "subtitle"))
        for caption, key in (("Description", "description"), ("My review", "review")):
            if movie.get(key):
                text.addSpacing(14)
                text.addWidget(label(t(caption), "section"))
                paragraph = label(movie[key])
                paragraph.setTextFormat(Qt.PlainText)
                paragraph.setWordWrap(True)
                paragraph.setTextInteractionFlags(Qt.TextSelectableByMouse)
                text.addWidget(paragraph)
        text.addStretch()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(content)
        body.addWidget(scroll, 1)
        layout.addLayout(body, 1)
        done = QPushButton(t("Done"))
        done.setObjectName("primary")
        done.clicked.connect(self.accept)
        layout.addWidget(done, alignment=Qt.AlignRight)

    def showEvent(self, event):
        super().showEvent(event)
        fade_in(self)

def search_icon():
    pixmap = QPixmap(48, 48)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(QPen(QApplication.palette().text().color(), 3))
    painter.drawEllipse(8, 7, 23, 23)
    painter.drawLine(28, 28, 39, 39)
    painter.end()
    return QIcon(pixmap)

class SearchDialog(QDialog):
    def __init__(self, parent, movies, query=""):
        super().__init__(parent)
        self.movies = movies
        self.selected_movie = None
        self.setWindowTitle(t("Search") + " · MovieShelf")
        self.resize(720, 480)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        self.input = QLineEdit(query)
        self.input.setObjectName("bigSearch")
        self.input.setPlaceholderText(t("Search your collection…"))
        self.input.setClearButtonEnabled(True)
        layout.addWidget(self.input)
        self.count = label("", "subtitle")
        layout.addWidget(self.count)
        self.results = QListWidget()
        self.results.setStyleSheet("QListWidget { border: none; background: transparent; } QListWidget::item { padding: 14px; border-radius: 8px; }")
        layout.addWidget(self.results, 1)
        self.input.textChanged.connect(self.update_results)
        self.input.returnPressed.connect(self.open_selected)
        self.results.itemActivated.connect(self.open_selected)
        buttons = QHBoxLayout()
        buttons.addStretch()
        show = QPushButton(t("Show results in library"))
        show.setObjectName("primary")
        show.clicked.connect(self.accept)
        buttons.addWidget(show)
        layout.addLayout(buttons)
        self.update_results()

    def update_results(self):
        query = self.input.text().strip().casefold()
        self.results.clear()
        for movie in self.movies:
            text = " ".join(str(movie.get(key, "")) for key in ("title", "id", "year", "description", "review"))
            text += " " + " ".join(movie.get("genres", []) + movie.get("tags", []))
            if query in text.casefold():
                item = QListWidgetItem(f"{movie['title']}   ·   {movie['year']}   ·   #{movie['id']}")
                item.setData(Qt.UserRole, movie)
                self.results.addItem(item)
        self.count.setText(f"{self.results.count()} {t('results')} · {t('Enter to open, Esc to close')}")
        if self.results.count():
            self.results.setCurrentRow(0)

    def open_selected(self, *args):
        item = self.results.currentItem()
        if item:
            self.selected_movie = item.data(Qt.UserRole)
            self.accept()

    def showEvent(self, event):
        super().showEvent(event)
        self.input.setFocus()
        fade_in(self)

class CollectionManager(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle(t("Manage collections") + " · MovieShelf")
        self.resize(470, 400)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.addWidget(label(t("Collections"), "title"))
        self.items = QListWidget()
        layout.addWidget(self.items, 1)
        buttons = QHBoxLayout()
        for title, handler in (("New collection", self.create), ("Rename", self.rename), ("Delete", self.delete)):
            button = QPushButton(t(title))
            button.clicked.connect(handler)
            buttons.addWidget(button)
        layout.addLayout(buttons)
        self.refresh()

    def refresh(self, selected_id=None):
        self.items.clear()
        for collection in store.load_collections():
            item = QListWidgetItem(collection["name"])
            item.setData(Qt.UserRole, collection["id"])
            self.items.addItem(item)
            if collection["id"] == selected_id:
                self.items.setCurrentItem(item)

    def selected(self):
        item = self.items.currentItem()
        return (item.data(Qt.UserRole), item.text()) if item else (None, None)

    def create(self):
        name, accepted = QInputDialog.getText(self, t("New collection"), t("Collection name"))
        if not accepted:
            return
        try:
            collection = store.create_collection(name)
            self.refresh(collection["id"])
        except (OSError, ValueError) as error:
            QMessageBox.warning(self, t("Could not change collection"), t(str(error)))

    def rename(self):
        collection_id, old_name = self.selected()
        if collection_id is None:
            return
        name, accepted = QInputDialog.getText(self, t("Rename collection"), t("Collection name"), text=old_name)
        if not accepted:
            return
        try:
            store.rename_collection(collection_id, name)
            self.refresh(collection_id)
        except (OSError, ValueError) as error:
            QMessageBox.warning(self, t("Could not change collection"), t(str(error)))

    def delete(self):
        collection_id, name = self.selected()
        if collection_id is None:
            return
        answer = QMessageBox.question(self, t("Delete collection?"), t("Delete “{name}”? Films will stay in your library.", name=name),
                                      QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if answer != QMessageBox.Yes:
            return
        try:
            store.delete_collection(collection_id)
            self.refresh()
        except (OSError, ValueError) as error:
            QMessageBox.warning(self, t("Could not change collection"), t(str(error)))

class SettingsDialog(QDialog):
    def __init__(self, parent, card_size):
        super().__init__(parent)
        self.setWindowTitle(t("Settings") + " · MovieShelf")
        self.resize(520, 420)
        self.values = dict(parent.preferences)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 26, 28, 24)
        layout.setSpacing(18)
        layout.addWidget(label(t("Settings"), "title"))
        form = QFormLayout()
        form.setVerticalSpacing(16)
        self.theme = QComboBox()
        self.theme.addItem(t("Dark"), "dark")
        self.theme.addItem(t("Light"), "light")
        self.theme.setCurrentIndex(0 if self.values["theme"] == "dark" else 1)
        form.addRow(t("Appearance"), self.theme)
        self.language = QComboBox()
        self.language.addItem("English", "en")
        self.language.addItem("Русский", "ru")
        self.language.addItem("Қазақша", "kk")
        self.language.setCurrentIndex(self.language.findData(self.values["language"]))
        form.addRow(t("Language"), self.language)
        self.motion = QCheckBox(t("Smooth transitions"))
        self.motion.setChecked(self.values["animations"])
        form.addRow(t("Animations"), self.motion)
        self.stats = QCheckBox(t("Show collection statistics"))
        self.stats.setChecked(self.values["show_statistics"])
        form.addRow(t("Library"), self.stats)
        self.size = QSlider(Qt.Horizontal)
        self.size.setRange(155, 245)
        self.size.setValue(card_size)
        form.addRow(t("Poster size"), self.size)
        layout.addLayout(form)
        backup = QPushButton(t("Export library backup…"))
        backup.clicked.connect(self.backup)
        layout.addWidget(backup)
        layout.addStretch()
        buttons = QHBoxLayout()
        buttons.addStretch()
        cancel = QPushButton(t("Cancel"))
        cancel.clicked.connect(self.reject)
        buttons.addWidget(cancel)
        save = QPushButton(t("Save and apply"))
        save.setObjectName("primary")
        save.clicked.connect(self.save)
        buttons.addWidget(save)
        layout.addLayout(buttons)
        layout.addWidget(label(f"MovieShelf {QApplication.instance().applicationVersion()}", "subtitle"))

    def save(self):
        self.values.update(theme=self.theme.currentData(), language=self.language.currentData(),
                           animations=self.motion.isChecked(), show_statistics=self.stats.isChecked(), card_size=self.size.value())
        try:
            preferences.save(self.values)
        except OSError as error:
            QMessageBox.warning(self, t("Cannot save settings"), str(error))
            return
        self.accept()

    def backup(self):
        filename, _ = QFileDialog.getSaveFileName(self, t("Export backup"), "MovieShelf-backup.zip", "ZIP archive (*.zip)")
        if not filename:
            return
        try:
            target = Path(filename)
            descriptor, name = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=target.parent)
            os.close(descriptor)
            temporary = Path(name)
            try:
                with store._collection_lock():
                    movies = store.load_movies()
                    with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED) as archive:
                        import json
                        archive.writestr("movies.json", json.dumps(movies, ensure_ascii=False, indent=2))
                        if store.COUNTER_FILE.is_file():
                            archive.write(store.COUNTER_FILE, store.COUNTER_FILE.name)
                        if store.COLLECTIONS_FILE.is_file():
                            archive.write(store.COLLECTIONS_FILE, store.COLLECTIONS_FILE.name)
                        paths = {store.poster_path(movie) for movie in movies} - {None}
                        for path in paths:
                            archive.write(path, path.relative_to(store.BASE_DIR).as_posix())
                os.replace(temporary, target)
            finally:
                temporary.unlink(missing_ok=True)
            QMessageBox.information(self, t("Backup ready"), t("Your films, reviews and posters have been exported."))
        except (OSError, ValueError) as error:
            QMessageBox.warning(self, t("Cannot export backup"), str(error))

    def showEvent(self, event):
        super().showEvent(event)
        fade_in(self)
