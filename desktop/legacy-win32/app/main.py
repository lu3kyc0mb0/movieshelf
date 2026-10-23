import sys
from pathlib import Path
from PySide2.QtCore import Qt, QTimer, QSize
from PySide2.QtGui import QIcon, QKeySequence
from PySide2.QtWidgets import (
    QShortcut,
    QApplication, QComboBox, QDialog, QFrame, QGridLayout, QHBoxLayout,
    QLabel, QLineEdit, QMainWindow, QMessageBox, QPushButton, QScrollArea,
    QSlider, QVBoxLayout, QWidget,
)
import movie_store as store
from editor import MovieEditor, label
from posters import PosterView
from theme import apply_theme
import preferences
from motion import fade_in
from panels import SearchDialog, SettingsDialog, MoviePreview, search_icon

class MovieCard(QFrame):
    def __init__(self, movie, size, open_movie):
        super().__init__()
        self.setObjectName("card")
        self.setFixedWidth(size)
        self.movie = movie
        self.open_movie = open_movie
        self.setCursor(Qt.PointingHandCursor)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(9, 9, 9, 12)
        layout.setSpacing(6)
        poster = PosterView(store.poster_path(movie), movie.get("poster_crop"))
        poster.setFixedSize(size-20, round((size-20)*1.5))
        poster.clicked.connect(lambda: open_movie(movie))
        layout.addWidget(poster)
        title = label(str(movie["title"]))
        title.setStyleSheet("font-weight: 650; font-size: 14px;")
        title.setToolTip(str(movie["title"]))
        title.setText(title.fontMetrics().elidedText(str(movie["title"]), Qt.ElideRight, size-20))
        layout.addWidget(title)
        row = QHBoxLayout()
        row.addWidget(label(f"{movie['year']}  ·  #{movie['id']}", "subtitle"))
        row.addStretch()
        if movie.get("rating"):
            row.addWidget(label(f"{movie['rating']}/10", "rating"))
        layout.addLayout(row)
        state = "Watched" if movie.get("status") == "watched" else "Want to watch"
        if movie.get("favorite"):
            state += "  ·  Favorite"
        layout.addWidget(label(state, "subtitle"))

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.open_movie(self.movie)

class MovieShelf(QMainWindow):
    VIEWS = ("Library", "Watchlist", "Watched", "Favorites", "My reviews")

    def __init__(self):
        super().__init__()
        self.setWindowTitle("MovieShelf")
        self.resize(1220, 830)
        self.setMinimumSize(620, 460)
        self.movies = []
        self.view = "Library"
        self.columns = 0
        self.ready = False
        try:
            self.preferences = preferences.load()
            self.preferences_error = None
        except (ValueError, OSError) as error:
            self.preferences = dict(preferences.DEFAULTS)
            self.preferences_error = str(error)
            QTimer.singleShot(0, lambda: QMessageBox.warning(self, "Settings could not be loaded", self.preferences_error + "\nYour settings file was left unchanged."))
        QApplication.instance().setProperty("movieshelf_animations", self.preferences["animations"])
        self._render_generation = 0
        self._render_signature = None
        self.reflow = QTimer(self)
        self.reflow.setSingleShot(True)
        self.reflow.setInterval(80)
        self.reflow.timeout.connect(self.render)
        root = QWidget()
        self.setCentralWidget(root)
        outer = QHBoxLayout(root)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(214)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(20, 34, 20, 20)
        side.setSpacing(5)
        side.addWidget(label("MovieShelf", "brand"))
        side.addSpacing(34)
        side.addWidget(label("COLLECTION", "eyebrow"))
        side.addSpacing(8)
        self.nav = {}
        for name in self.VIEWS:
            button = QPushButton(name)
            button.setObjectName("nav")
            button.setCheckable(True)
            button.clicked.connect(lambda checked=False, value=name: self.change_view(value))
            side.addWidget(button)
            self.nav[name] = button
        side.addStretch()
        settings = QPushButton("Settings")
        settings.setObjectName("nav")
        settings.clicked.connect(self.open_settings)
        side.addWidget(settings)
        self.collection_count = label("", "subtitle")
        side.addWidget(self.collection_count)
        outer.addWidget(sidebar)

        main = QVBoxLayout()
        main.setContentsMargins(32, 30, 32, 16)
        main.setSpacing(18)
        heading = QHBoxLayout()
        text = QVBoxLayout()
        text.setSpacing(5)
        self.title = label("Library", "title")
        text.addWidget(self.title)
        heading.addLayout(text)
        heading.addStretch()
        self.search_button = QPushButton()
        self.search_button.setIcon(search_icon())
        self.search_button.setIconSize(QSize(22, 22))
        self.search_button.setFixedSize(42, 38)
        self.search_button.setToolTip("Search (Ctrl+F)")
        self.search_button.setAccessibleName("Search collection")
        self.search_button.clicked.connect(self.open_search)
        heading.addWidget(self.search_button)
        add = QPushButton("+  Add movie")
        add.setObjectName("primary")
        add.clicked.connect(lambda: self.edit_movie())
        heading.addWidget(add)
        main.addLayout(heading)

        metrics = QHBoxLayout()
        metrics.setSpacing(12)
        self.metrics = []
        for caption in ("In your library", "Watched", "Average rating"):
            frame = QFrame()
            frame.setObjectName("stat")
            layout = QVBoxLayout(frame)
            layout.setContentsMargins(17, 12, 17, 12)
            number = label("—", "metric")
            self.metrics.append(number)
            layout.addWidget(number)
            layout.addWidget(label(caption, "subtitle"))
            metrics.addWidget(frame)
        self.statistics = QWidget()
        self.statistics.setLayout(metrics)
        self.statistics.setVisible(self.preferences["show_statistics"])
        main.addWidget(self.statistics)

        controls = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setParent(root)
        self.search.hide()
        self.search.setPlaceholderText("Search titles, IDs, years and notes")
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self.render)
        self.query_button = QPushButton()
        self.query_button.hide()
        self.query_button.clicked.connect(self.clear_search)
        controls.addWidget(self.query_button)
        controls.addStretch()
        self.sort = QComboBox()
        self.sort.addItems(["Recently added", "Title A–Z", "Highest rated", "Newest release"])
        self.sort.currentIndexChanged.connect(self.render)
        controls.addWidget(self.sort)
        main.addLayout(controls)
        shelf = QHBoxLayout()
        self.results_label = label("", "section")
        shelf.addWidget(self.results_label)
        shelf.addStretch()
        shelf.addWidget(label("Poster size", "subtitle"))
        self.card_size = QSlider(Qt.Horizontal)
        self.card_size.setRange(155, 245)
        self.card_size.setValue(self.preferences["card_size"])
        self.card_size.setFixedWidth(100)
        self.card_size.valueChanged.connect(lambda: self.reflow.start())
        shelf.addWidget(self.card_size)
        main.addLayout(shelf)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.host = QWidget()
        self.host.setStyleSheet("background: transparent;")
        self.grid = QGridLayout(self.host)
        self.grid.setContentsMargins(0, 0, 8, 8)
        self.grid.setSpacing(18)
        self.grid.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self.scroll.setWidget(self.host)
        main.addWidget(self.scroll, 1)
        outer.addLayout(main, 1)
        self.statusBar().showMessage("Select a movie to edit its details, review and artwork.")
        QShortcut(QKeySequence.New, self, activated=lambda: self.edit_movie())
        QShortcut(QKeySequence.Find, self, activated=self.open_search)
        self.ready = True
        self.reload()

    def reload(self):
        try:
            self.movies = store.load_movies()
        except (ValueError, OSError) as error:
            QMessageBox.critical(self, "Could not open collection", str(error))
            return
        self.metrics[0].setText(str(len(self.movies)))
        self.metrics[1].setText(str(sum(m.get("status") == "watched" for m in self.movies)))
        ratings = [m["rating"] for m in self.movies if m.get("rating")]
        self.metrics[2].setText(f"{sum(ratings)/len(ratings):.1f} / 10" if ratings else "—")
        self.collection_count.setText(f"{len(self.movies)} film{'s' if len(self.movies) != 1 else ''} · stored locally")
        for name, button in self.nav.items():
            button.setChecked(name == self.view)
        self._render_signature = None
        self.render()

    def change_view(self, name):
        self.view = name
        self.title.setText(name)
        for key, button in self.nav.items():
            button.setChecked(key == name)
        self.render()
        fade_in(self.host)

    def open_search(self):
        dialog = SearchDialog(self, self.movies, self.search.text())
        if dialog.exec_() == QDialog.Accepted:
            if dialog.selected_movie:
                self.edit_movie(dialog.selected_movie)
            else:
                self.search.setText(dialog.input.text())
                self.query_button.setText(f"Search: {dialog.input.text()}  ×")
                self.query_button.setVisible(bool(dialog.input.text()))
                self.change_view("Library")
        dialog.deleteLater()

    def clear_search(self):
        self.search.clear()
        self.query_button.hide()

    def open_settings(self):
        dialog = SettingsDialog(self, self.card_size.value())
        if dialog.exec_() == QDialog.Accepted:
            self.preferences = dialog.values
            self.preferences_error = None
            QApplication.instance().setProperty("movieshelf_animations", self.preferences["animations"])
            apply_theme(QApplication.instance(), self.preferences["theme"])
            self.search_button.setIcon(search_icon())
            self.statistics.setVisible(self.preferences["show_statistics"])
            self.card_size.setValue(self.preferences["card_size"])
            self.render()
            fade_in(self.host)
            self.statusBar().showMessage("Settings saved.", 4000)
        dialog.deleteLater()

    def filtered_movies(self):
        query = self.search.text().strip().casefold()
        result = []
        for movie in self.movies:
            if self.view == "Watchlist" and movie.get("status", "watchlist") != "watchlist":
                continue
            if self.view == "Watched" and movie.get("status") != "watched":
                continue
            if self.view == "Favorites" and not movie.get("favorite"):
                continue
            if self.view == "My reviews" and not (movie.get("review", "").strip() or movie.get("rating")):
                continue
            searchable = " ".join(str(movie.get(key, "")) for key in ("title", "id", "year", "description", "review"))
            if query in searchable.casefold():
                result.append(movie)
        keys = [lambda m: -int(m["id"]), lambda m: m["title"].casefold(),
                lambda m: -m.get("rating", 0), lambda m: -int(m["year"])]
        return sorted(result, key=keys[self.sort.currentIndex()])

    def render(self):
        if not self.ready:
            return
        size = self.card_size.value()
        columns = max(1, (self.scroll.viewport().width()-8+18)//(size+18))
        signature = (self.view, self.search.text(), self.sort.currentIndex(), size, columns)
        if signature == self._render_signature:
            return
        self._render_signature = signature
        self._render_generation += 1
        while self.grid.count():
            item = self.grid.takeAt(0)
            if item.widget():
                item.widget().hide()
                item.widget().deleteLater()
        results = self.filtered_movies()
        self.results_label.setText(f"{len(results)} film{'s' if len(results) != 1 else ''}")
        self.columns = columns
        self._pending_results = results
        self._pending_index = 0
        self._render_batch(self._render_generation)
        if not results:
            empty = QFrame()
            layout = QVBoxLayout(empty)
            layout.setContentsMargins(10, 50, 10, 20)
            layout.addWidget(label("A little room for your next discovery.", "section"))
            layout.addWidget(label("Try another search, or add a film to your collection.", "subtitle"))
            self.grid.addWidget(empty, 0, 0)

    def _render_batch(self, generation):
        if generation != self._render_generation:
            return
        end = min(self._pending_index + 24, len(self._pending_results))
        for i in range(self._pending_index, end):
            movie = self._pending_results[i]
            size = self.card_size.value()
            card = MovieCard(movie, size, self.edit_movie)
            if self.view == "My reviews":
                excerpt = label(movie.get("review", "")[:160] or "No written review yet.", "subtitle")
                excerpt.setWordWrap(True)
                card.layout().addWidget(excerpt)
            self.grid.addWidget(card, i//self.columns, i%self.columns)
        self._pending_index = end
        if end < len(self._pending_results):
            QTimer.singleShot(1, lambda: self._render_batch(generation))

    def edit_movie(self, movie=None):
        editor = MovieEditor(self, movie)
        if movie:
            delete = QPushButton("Delete movie")
            delete.setObjectName("danger")
            editor.layout().insertWidget(editor.layout().count()-1, delete, alignment=Qt.AlignLeft)
            delete.clicked.connect(lambda: self.delete_movie(movie, editor))
        if editor.exec_() == QDialog.Accepted:
            self.reload()
            self.statusBar().showMessage("Changes saved.", 5000)
            if editor.saved_movie and editor.view_after_save:
                self.clear_search()
                self.change_view("Library")
                preview = MoviePreview(self, editor.saved_movie)
                preview.exec_()
                preview.deleteLater()
        editor.deleteLater()

    def delete_movie(self, movie, editor):
        answer = QMessageBox.question(editor, "Delete movie", f"Delete “{movie['title']}” and its review?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if answer != QMessageBox.Yes:
            return
        try:
            store.delete_movie(movie["id"])
        except (ValueError, OSError) as error:
            QMessageBox.warning(editor, "Could not delete", str(error))
            return
        editor.saved_movie = None
        editor.view_after_save = False
        editor.accept()

    def closeEvent(self, event):
        if self.preferences_error:
            super().closeEvent(event)
            return
        values = dict(self.preferences)
        values["card_size"] = self.card_size.value()
        try:
            preferences.save(values)
        except OSError as error:
            choice = QMessageBox.question(self, "Could not save preferences", f"{error}\nClose without saving preferences?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if choice != QMessageBox.Yes:
                event.ignore()
                return
        super().closeEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if getattr(self, "ready", False):
            self.reflow.start()

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("MovieShelf")
    app.setWindowIcon(QIcon(str(Path(__file__).resolve().parent / "assets" / "icon-preview.png")))
    window = MovieShelf()
    apply_theme(app, window.preferences["theme"])
    window.show()
    return app.exec_()

if __name__ == "__main__":
    sys.exit(main())
