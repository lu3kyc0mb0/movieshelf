import sys
from pathlib import Path
from PySide2.QtCore import Qt, QTimer, QSize
from PySide2.QtGui import QIcon, QKeySequence
from PySide2.QtWidgets import (
    QShortcut,
    QApplication, QComboBox, QDialog, QFrame, QGridLayout, QHBoxLayout,
    QLabel, QLineEdit, QMainWindow, QMessageBox, QPushButton, QScrollArea,
    QSlider, QSpinBox, QVBoxLayout, QWidget,
)
import movie_store as store
from editor import MovieEditor, label
from posters import PosterView
from theme import apply_theme
import preferences
from motion import fade_in
from panels import CollectionManager, SearchDialog, SettingsDialog, MoviePreview, search_icon
from i18n import film_count, set_language, t

APP_VERSION = "1.3.0"

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
        state = t("Watched" if movie.get("status") == "watched" else "Want to watch")
        if movie.get("favorite"):
            state += "  ·  " + t("Favorite")
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
        self.collections = []
        self.view = "Library"
        self.columns = 0
        self.ready = False
        try:
            self.preferences = preferences.load()
            self.preferences_error = None
        except (ValueError, OSError) as error:
            self.preferences = dict(preferences.DEFAULTS)
            self.preferences_error = str(error)
            QTimer.singleShot(0, lambda: QMessageBox.warning(self, t("Settings could not be loaded"), self.preferences_error + "\n" + t("Your settings file was left unchanged.")))
        set_language(self.preferences["language"])
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
        self.eyebrow = label(t("COLLECTION"), "eyebrow")
        side.addWidget(self.eyebrow)
        side.addSpacing(8)
        self.nav = {}
        for name in self.VIEWS:
            button = QPushButton(t(name))
            button.setObjectName("nav")
            button.setCheckable(True)
            button.clicked.connect(lambda checked=False, value=name: self.change_view(value))
            side.addWidget(button)
            self.nav[name] = button
        side.addSpacing(20)
        self.custom_heading = label(t("CUSTOM COLLECTIONS"), "eyebrow")
        side.addWidget(self.custom_heading)
        custom_host = QWidget()
        self.custom_layout = QVBoxLayout(custom_host)
        self.custom_layout.setSpacing(4)
        self.custom_layout.setContentsMargins(0, 0, 0, 0)
        self.custom_layout.setAlignment(Qt.AlignTop)
        custom_scroll = QScrollArea()
        custom_scroll.setWidgetResizable(True)
        custom_scroll.setMaximumHeight(180)
        custom_scroll.setFrameShape(QFrame.NoFrame)
        custom_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        custom_scroll.setWidget(custom_host)
        side.addWidget(custom_scroll)
        self.collection_buttons = {}
        self.manage_button = QPushButton(t("Manage collections"))
        self.manage_button.setObjectName("nav")
        self.manage_button.clicked.connect(self.manage_collections)
        side.addWidget(self.manage_button)
        side.addStretch()
        self.settings_button = QPushButton(t("Settings"))
        self.settings_button.setObjectName("nav")
        self.settings_button.clicked.connect(self.open_settings)
        side.addWidget(self.settings_button)
        self.collection_count = label("", "subtitle")
        side.addWidget(self.collection_count)
        outer.addWidget(sidebar)

        main = QVBoxLayout()
        main.setContentsMargins(32, 30, 32, 16)
        main.setSpacing(18)
        heading = QHBoxLayout()
        text = QVBoxLayout()
        text.setSpacing(5)
        self.title = label(t("Library"), "title")
        text.addWidget(self.title)
        heading.addLayout(text)
        heading.addStretch()
        self.search_button = QPushButton()
        self.search_button.setIcon(search_icon())
        self.search_button.setIconSize(QSize(22, 22))
        self.search_button.setFixedSize(42, 38)
        self.search_button.setToolTip(t("Search (Ctrl+F)"))
        self.search_button.setAccessibleName(t("Search collection"))
        self.search_button.clicked.connect(self.open_search)
        heading.addWidget(self.search_button)
        self.add_button = QPushButton(t("+  Add movie"))
        self.add_button.setObjectName("primary")
        self.add_button.clicked.connect(lambda: self.edit_movie())
        heading.addWidget(self.add_button)
        main.addLayout(heading)

        metrics = QHBoxLayout()
        metrics.setSpacing(12)
        self.metrics = []
        self.metric_captions = []
        for caption in ("In your library", "Watched", "Average rating"):
            frame = QFrame()
            frame.setObjectName("stat")
            layout = QVBoxLayout(frame)
            layout.setContentsMargins(17, 12, 17, 12)
            number = label("—", "metric")
            self.metrics.append(number)
            layout.addWidget(number)
            caption_label = label(t(caption), "subtitle")
            self.metric_captions.append(caption_label)
            layout.addWidget(caption_label)
            metrics.addWidget(frame)
        self.statistics = QWidget()
        self.statistics.setLayout(metrics)
        self.statistics.setVisible(self.preferences["show_statistics"])
        main.addWidget(self.statistics)

        controls = QHBoxLayout()
        self.search = QLineEdit()
        self.search.setParent(root)
        self.search.hide()
        self.search.setPlaceholderText(t("Search titles, IDs, years and notes"))
        self.search.setClearButtonEnabled(True)
        self.search.textChanged.connect(self.render)
        self.query_button = QPushButton()
        self.query_button.hide()
        self.query_button.clicked.connect(self.clear_search)
        controls.addWidget(self.query_button)
        controls.addStretch()
        self.sort = QComboBox()
        self.sort.addItems([t(name) for name in ("Recently added", "Title A–Z", "Highest rated", "Newest release")])
        self.sort.currentIndexChanged.connect(self.render)
        controls.addWidget(self.sort)
        main.addLayout(controls)
        self.filter_toggle = QPushButton(t("Filters"))
        self.filter_toggle.setCheckable(True)
        self.filter_toggle.toggled.connect(self.toggle_filters)
        main.addWidget(self.filter_toggle, alignment=Qt.AlignLeft)
        self.filter_panel = QFrame()
        self.filter_panel.setObjectName("stat")
        filter_layout = QVBoxLayout(self.filter_panel)
        self.filter_labels = {}
        first_filters = QHBoxLayout()
        self.year_from = QSpinBox()
        self.year_to = QSpinBox()
        for key, widget in (("From year", self.year_from), ("To year", self.year_to)):
            widget.setRange(0, 2100)
            widget.setSpecialValueText(t("Any"))
            widget.valueChanged.connect(self.render)
            self.add_filter_control(first_filters, key, widget)
        self.rating_from = QSpinBox()
        self.rating_to = QSpinBox()
        for key, widget in (("Min rating", self.rating_from), ("Max rating", self.rating_to)):
            widget.setRange(0, 10)
            widget.setSpecialValueText(t("Any"))
            widget.valueChanged.connect(self.render)
            self.add_filter_control(first_filters, key, widget)
        filter_layout.addLayout(first_filters)
        second_filters = QHBoxLayout()
        self.status_filter = QComboBox()
        self.favorite_filter = QComboBox()
        self.genre_filter = QComboBox()
        self.tag_filter = QComboBox()
        self.collection_filter = QComboBox()
        third_filters = QHBoxLayout()
        for key, widget in (("Status", self.status_filter), ("Favorite", self.favorite_filter),
                            ("Genre", self.genre_filter), ("Tag", self.tag_filter),
                            ("Custom collection", self.collection_filter)):
            widget.currentIndexChanged.connect(self.render)
            self.add_filter_control(third_filters if key in ("Tag", "Custom collection") else second_filters, key, widget)
        filter_layout.addLayout(second_filters)
        filter_layout.addLayout(third_filters)
        reset = QPushButton(t("Reset filters"))
        reset.clicked.connect(self.reset_filters)
        self.reset_button = reset
        filter_layout.addWidget(reset, alignment=Qt.AlignRight)
        self.filter_panel.hide()
        main.addWidget(self.filter_panel)
        shelf = QHBoxLayout()
        self.results_label = label("", "section")
        shelf.addWidget(self.results_label)
        shelf.addStretch()
        self.poster_size_label = label(t("Poster size"), "subtitle")
        shelf.addWidget(self.poster_size_label)
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
        self.statusBar().showMessage(t("Select a movie to edit its details, review and artwork."))
        QShortcut(QKeySequence.New, self, activated=lambda: self.edit_movie())
        QShortcut(QKeySequence.Find, self, activated=self.open_search)
        self.ready = True
        self.reload()

    def add_filter_control(self, row, key, widget):
        column = QVBoxLayout()
        caption = label(t(key), "subtitle")
        self.filter_labels[key] = caption
        column.addWidget(caption)
        column.addWidget(widget)
        row.addLayout(column, 1)

    def toggle_filters(self, visible):
        self.filter_panel.setVisible(visible)
        self.filter_toggle.setText(t("Hide filters" if visible else "Filters"))

    def reset_filters(self):
        for widget in (self.year_from, self.year_to, self.rating_from, self.rating_to):
            widget.setValue(0)
        for widget in (self.status_filter, self.favorite_filter, self.genre_filter, self.tag_filter, self.collection_filter):
            widget.setCurrentIndex(0)
        self.render()

    def refresh_filter_options(self):
        genres = {name.casefold(): name for movie in reversed(self.movies) for name in movie.get("genres", [])}
        tags = {name.casefold(): name for movie in reversed(self.movies) for name in movie.get("tags", [])}
        options = (
            (self.status_filter, [(t("All statuses"), None), (t("Want to watch"), "watchlist"), (t("Watched"), "watched")]),
            (self.favorite_filter, [(t("Any"), None), (t("Favorites only"), True), (t("Not favorites"), False)]),
            (self.genre_filter, [(t("Any genre"), None)] + [(value, value.casefold()) for value in sorted(genres.values(), key=str.casefold)]),
            (self.tag_filter, [(t("Any tag"), None)] + [(value, value.casefold()) for value in sorted(tags.values(), key=str.casefold)]),
            (self.collection_filter, [(t("Any collection"), None)] + [(item["name"], item["id"]) for item in self.collections]),
        )
        for widget, entries in options:
            selected = widget.currentData()
            widget.blockSignals(True)
            widget.clear()
            for title, value in entries:
                widget.addItem(title, value)
            index = widget.findData(selected)
            widget.setCurrentIndex(index if index >= 0 else 0)
            widget.blockSignals(False)

    def refresh_collection_buttons(self):
        while self.custom_layout.count():
            item = self.custom_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self.collection_buttons = {}
        for collection in self.collections:
            button = QPushButton(collection["name"])
            button.setObjectName("nav")
            button.setCheckable(True)
            view_name = "collection:" + collection["id"]
            button.clicked.connect(lambda checked=False, value=view_name: self.change_view(value))
            button.setChecked(self.view == view_name)
            self.custom_layout.addWidget(button)
            self.collection_buttons[collection["id"]] = button

    def view_title(self):
        if self.view.startswith("collection:"):
            collection_id = self.view.split(":", 1)[1]
            return next((item["name"] for item in self.collections if item["id"] == collection_id), t("Library"))
        return t(self.view)

    def manage_collections(self):
        dialog = CollectionManager(self)
        dialog.exec_()
        dialog.deleteLater()
        self.reload()

    def retranslate(self):
        self.eyebrow.setText(t("COLLECTION"))
        self.custom_heading.setText(t("CUSTOM COLLECTIONS"))
        for name, button in self.nav.items():
            button.setText(t(name))
        self.manage_button.setText(t("Manage collections"))
        self.settings_button.setText(t("Settings"))
        self.title.setText(self.view_title())
        self.search_button.setToolTip(t("Search (Ctrl+F)"))
        self.search_button.setAccessibleName(t("Search collection"))
        self.add_button.setText(t("+  Add movie"))
        for key, caption in zip(("In your library", "Watched", "Average rating"), self.metric_captions):
            caption.setText(t(key))
        self.search.setPlaceholderText(t("Search titles, IDs, years and notes"))
        if self.search.text():
            self.query_button.setText(t("Search: {query}  ×", query=self.search.text()))
        for index, key in enumerate(("Recently added", "Title A–Z", "Highest rated", "Newest release")):
            self.sort.setItemText(index, t(key))
        self.filter_toggle.setText(t("Hide filters" if self.filter_toggle.isChecked() else "Filters"))
        self.reset_button.setText(t("Reset filters"))
        for key, caption in self.filter_labels.items():
            caption.setText(t(key))
        for widget in (self.year_from, self.year_to, self.rating_from, self.rating_to):
            widget.setSpecialValueText(t("Any"))
        self.poster_size_label.setText(t("Poster size"))
        self.collection_count.setText(f"{film_count(len(self.movies))} · {t('stored locally')}")
        self.statusBar().showMessage(t("Select a movie to edit its details, review and artwork."))
        self._render_signature = None
        self.refresh_filter_options()
        self.render()

    def reload(self):
        try:
            self.movies = store.load_movies()
            self.collections = store.load_collections()
        except (ValueError, OSError) as error:
            QMessageBox.critical(self, t("Could not open collection"), str(error))
            return
        self.metrics[0].setText(str(len(self.movies)))
        self.metrics[1].setText(str(sum(m.get("status") == "watched" for m in self.movies)))
        ratings = [m["rating"] for m in self.movies if m.get("rating")]
        self.metrics[2].setText(f"{sum(ratings)/len(ratings):.1f} / 10" if ratings else "—")
        self.collection_count.setText(f"{film_count(len(self.movies))} · {t('stored locally')}")
        if self.view.startswith("collection:") and self.view.split(":", 1)[1] not in {item["id"] for item in self.collections}:
            self.view = "Library"
        self.title.setText(self.view_title())
        for name, button in self.nav.items():
            button.setChecked(name == self.view)
        self.refresh_collection_buttons()
        self.refresh_filter_options()
        self._render_signature = None
        self.render()

    def change_view(self, name):
        self.view = name
        self.title.setText(self.view_title())
        for key, button in self.nav.items():
            button.setChecked(key == name)
        for collection_id, button in self.collection_buttons.items():
            button.setChecked(name == "collection:" + collection_id)
        self.render()
        fade_in(self.host)

    def open_search(self):
        dialog = SearchDialog(self, self.movies, self.search.text())
        if dialog.exec_() == QDialog.Accepted:
            if dialog.selected_movie:
                self.edit_movie(dialog.selected_movie)
            else:
                self.search.setText(dialog.input.text())
                self.query_button.setText(t("Search: {query}  ×", query=dialog.input.text()))
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
            set_language(self.preferences["language"])
            QApplication.instance().setProperty("movieshelf_animations", self.preferences["animations"])
            apply_theme(QApplication.instance(), self.preferences["theme"])
            self.search_button.setIcon(search_icon())
            self.statistics.setVisible(self.preferences["show_statistics"])
            self.card_size.setValue(self.preferences["card_size"])
            self.retranslate()
            fade_in(self.host)
            self.statusBar().showMessage(t("Settings saved."), 4000)
        dialog.deleteLater()

    def filtered_movies(self):
        query = self.search.text().strip().casefold()
        result = []
        selected_genre = self.genre_filter.currentData()
        selected_tag = self.tag_filter.currentData()
        selected_collection = self.collection_filter.currentData()
        status = self.status_filter.currentData()
        favorite = self.favorite_filter.currentData()
        current_collection = self.view.split(":", 1)[1] if self.view.startswith("collection:") else None
        for movie in self.movies:
            if self.view == "Watchlist" and movie.get("status", "watchlist") != "watchlist":
                continue
            if self.view == "Watched" and movie.get("status") != "watched":
                continue
            if self.view == "Favorites" and not movie.get("favorite"):
                continue
            if self.view == "My reviews" and not (movie.get("review", "").strip() or movie.get("rating")):
                continue
            if current_collection and current_collection not in movie.get("collections", []):
                continue
            if self.year_from.value() and movie["year"] < self.year_from.value():
                continue
            if self.year_to.value() and movie["year"] > self.year_to.value():
                continue
            rating = movie.get("rating", 0)
            if (self.rating_from.value() or self.rating_to.value()) and not rating:
                continue
            if self.rating_from.value() and rating < self.rating_from.value():
                continue
            if self.rating_to.value() and rating > self.rating_to.value():
                continue
            if status is not None and movie.get("status", "watchlist") != status:
                continue
            if favorite is not None and bool(movie.get("favorite")) != favorite:
                continue
            if selected_genre is not None and selected_genre not in {name.casefold() for name in movie.get("genres", [])}:
                continue
            if selected_tag is not None and selected_tag not in {name.casefold() for name in movie.get("tags", [])}:
                continue
            if selected_collection is not None and selected_collection not in movie.get("collections", []):
                continue
            searchable = " ".join(str(movie.get(key, "")) for key in ("title", "id", "year", "description", "review"))
            searchable += " " + " ".join(movie.get("genres", []) + movie.get("tags", []))
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
        signature = (self.view, self.search.text(), self.sort.currentIndex(), size, columns,
                     self.year_from.value(), self.year_to.value(), self.rating_from.value(), self.rating_to.value(),
                     self.status_filter.currentData(), self.favorite_filter.currentData(), self.genre_filter.currentData(),
                     self.tag_filter.currentData(), self.collection_filter.currentData())
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
        self.results_label.setText(film_count(len(results)))
        self.columns = columns
        self._pending_results = results
        self._pending_index = 0
        self._render_batch(self._render_generation)
        if not results:
            empty = QFrame()
            layout = QVBoxLayout(empty)
            layout.setContentsMargins(10, 50, 10, 20)
            layout.addWidget(label(t("A little room for your next discovery."), "section"))
            layout.addWidget(label(t("Try another search, or add a film to your collection."), "subtitle"))
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
                excerpt = label(movie.get("review", "")[:160] or t("No written review yet."), "subtitle")
                excerpt.setWordWrap(True)
                card.layout().addWidget(excerpt)
            self.grid.addWidget(card, i//self.columns, i%self.columns)
        self._pending_index = end
        if end < len(self._pending_results):
            QTimer.singleShot(1, lambda: self._render_batch(generation))

    def edit_movie(self, movie=None):
        editor = MovieEditor(self, movie)
        if movie:
            delete = QPushButton(t("Delete movie"))
            delete.setObjectName("danger")
            editor.layout().insertWidget(editor.layout().count()-1, delete, alignment=Qt.AlignLeft)
            delete.clicked.connect(lambda: self.delete_movie(movie, editor))
        if editor.exec_() == QDialog.Accepted:
            self.reload()
            self.statusBar().showMessage(t("Changes saved."), 5000)
            if editor.saved_movie and editor.view_after_save:
                self.clear_search()
                self.change_view("Library")
                preview = MoviePreview(self, editor.saved_movie)
                preview.exec_()
                preview.deleteLater()
        editor.deleteLater()

    def delete_movie(self, movie, editor):
        answer = QMessageBox.question(editor, t("Delete movie"), t("Delete “{title}” and its review?", title=movie["title"]),
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if answer != QMessageBox.Yes:
            return
        try:
            store.delete_movie(movie["id"])
        except (ValueError, OSError) as error:
            QMessageBox.warning(editor, t("Could not delete"), str(error))
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
            choice = QMessageBox.question(self, t("Could not save preferences"), f"{error}\n{t('Close without saving preferences?')}",
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
    app.setApplicationVersion(APP_VERSION)
    app.setWindowIcon(QIcon(str(Path(__file__).resolve().parent / "assets" / "icon-preview.png")))
    window = MovieShelf()
    apply_theme(app, window.preferences["theme"])
    window.show()
    return app.exec_()

if __name__ == "__main__":
    sys.exit(main())
