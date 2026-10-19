from pathlib import Path
import zipfile
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QDialog, QFileDialog, QFormLayout,
    QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QMessageBox,
    QPushButton, QSlider, QVBoxLayout, QScrollArea, QWidget,
)
import movie_store as store
import preferences
from editor import label
from motion import fade_in
from posters import PosterView


class MoviePreview(QDialog):
    def __init__(self, parent, movie):
        super().__init__(parent)
        self.setWindowTitle("Saved movie · MovieShelf")
        self.resize(800, 600)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 28, 28, 24)
        body = QHBoxLayout()
        body.setSpacing(28)
        poster = PosterView(store.poster_path(movie), movie.get("poster_crop"))
        poster.setFixedSize(260, 390)
        body.addWidget(poster, alignment=Qt.AlignmentFlag.AlignTop)
        content = QWidget()
        text = QVBoxLayout(content)
        title = label(movie["title"], "title")
        title.setWordWrap(True)
        text.addWidget(title)
        text.addWidget(label(f"{movie['year']}  ·  ID #{movie['id']}", "subtitle"))
        text.addWidget(label(f"{movie['rating']}/10" if movie.get("rating") else "Not rated", "rating"))
        text.addWidget(label("Watched" if movie.get("status") == "watched" else "Want to watch", "subtitle"))
        for caption, key in (("Description", "description"), ("My review", "review")):
            if movie.get(key):
                text.addSpacing(14)
                text.addWidget(label(caption, "section"))
                paragraph = label(movie[key])
                paragraph.setTextFormat(Qt.TextFormat.PlainText)
                paragraph.setWordWrap(True)
                paragraph.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
                text.addWidget(paragraph)
        text.addStretch()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(content)
        body.addWidget(scroll, 1)
        layout.addLayout(body, 1)
        done = QPushButton("Done")
        done.setObjectName("primary")
        done.clicked.connect(self.accept)
        layout.addWidget(done, alignment=Qt.AlignmentFlag.AlignRight)

    def showEvent(self, event):
        super().showEvent(event)
        fade_in(self)


def search_icon():
    pixmap = QPixmap(48, 48)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
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
        self.setWindowTitle("Search · MovieShelf")
        self.resize(720, 480)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        self.input = QLineEdit(query)
        self.input.setObjectName("bigSearch")
        self.input.setPlaceholderText("Search your collection…")
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
        show = QPushButton("Show results in library")
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
            if query in text.casefold():
                item = QListWidgetItem(f"{movie['title']}   ·   {movie['year']}   ·   #{movie['id']}")
                item.setData(Qt.ItemDataRole.UserRole, movie)
                self.results.addItem(item)
        self.count.setText(f"{self.results.count()} results · Enter to open, Esc to close")
        if self.results.count():
            self.results.setCurrentRow(0)

    def open_selected(self, *args):
        item = self.results.currentItem()
        if item:
            self.selected_movie = item.data(Qt.ItemDataRole.UserRole)
            self.accept()

    def showEvent(self, event):
        super().showEvent(event)
        self.input.setFocus()
        fade_in(self)


class SettingsDialog(QDialog):
    def __init__(self, parent, card_size):
        super().__init__(parent)
        self.setWindowTitle("Settings · MovieShelf")
        self.resize(520, 420)
        self.values = preferences.load()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(28, 26, 28, 24)
        layout.setSpacing(18)
        layout.addWidget(label("Settings", "title"))
        form = QFormLayout()
        form.setVerticalSpacing(16)
        self.theme = QComboBox()
        self.theme.addItems(["Dark", "Light"])
        self.theme.setCurrentIndex(0 if self.values["theme"] == "dark" else 1)
        form.addRow("Appearance", self.theme)
        self.motion = QCheckBox("Smooth transitions")
        self.motion.setChecked(self.values["animations"])
        form.addRow("Animations", self.motion)
        self.stats = QCheckBox("Show collection statistics")
        self.stats.setChecked(self.values["show_statistics"])
        form.addRow("Library", self.stats)
        self.size = QSlider(Qt.Orientation.Horizontal)
        self.size.setRange(155, 245)
        self.size.setValue(card_size)
        form.addRow("Poster size", self.size)
        layout.addLayout(form)
        backup = QPushButton("Export library backup…")
        backup.clicked.connect(self.backup)
        layout.addWidget(backup)
        layout.addStretch()
        buttons = QHBoxLayout()
        buttons.addStretch()
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        buttons.addWidget(cancel)
        save = QPushButton("Save and apply")
        save.setObjectName("primary")
        save.clicked.connect(self.save)
        buttons.addWidget(save)
        layout.addLayout(buttons)

    def save(self):
        self.values.update(theme=self.theme.currentText().lower(), animations=self.motion.isChecked(),
                           show_statistics=self.stats.isChecked(), card_size=self.size.value())
        try:
            preferences.save(self.values)
        except OSError as error:
            QMessageBox.warning(self, "Cannot save settings", str(error))
            return
        self.accept()

    def backup(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Export backup", "MovieShelf-backup.zip", "ZIP archive (*.zip)")
        if not filename:
            return
        try:
            movies = store.load_movies()
            with zipfile.ZipFile(filename, "w", zipfile.ZIP_DEFLATED) as archive:
                import json
                archive.writestr("movies.json", json.dumps(movies, ensure_ascii=False, indent=2))
                paths = {store.poster_path(movie) for movie in movies} - {None}
                for path in paths:
                    archive.write(path, path.relative_to(store.BASE_DIR).as_posix())
            QMessageBox.information(self, "Backup ready", "Your films, reviews and posters have been exported.")
        except (OSError, ValueError) as error:
            QMessageBox.warning(self, "Cannot export backup", str(error))

    def showEvent(self, event):
        super().showEvent(event)
        fade_in(self)
