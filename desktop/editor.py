import json
from PySide6.QtCore import Qt, QDate
from PySide6.QtGui import QImageReader, QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QFileDialog, QFormLayout, QHBoxLayout,
    QLabel, QLineEdit, QMessageBox, QPushButton, QScrollArea, QSlider, QSpinBox,
    QTabWidget, QTextEdit, QVBoxLayout, QWidget,
)
import movie_store as store
from posters import PosterView
from motion import fade_in
from i18n import t

def split_labels(text):
    result = []
    seen = set()
    for part in text.split(","):
        value = part.strip()
        if value and value.casefold() not in seen:
            result.append(value)
            seen.add(value.casefold())
    return result

def label(text, name=None):
    result = QLabel(text)
    if name:
        result.setObjectName(name)
    return result

class MovieEditor(QDialog):
    def __init__(self, parent=None, movie=None):
        super().__init__(parent)
        self.movie = movie or {}
        self.saved_movie = None
        self.view_after_save = False
        self.poster_source = None
        self.remove_poster = False
        self.available_collections = parent.collections if parent is not None and hasattr(parent, "collections") else store.load_collections()
        self.setWindowTitle(t("Movie details") + " · MovieShelf")
        self.resize(800, 670)
        self.setMinimumSize(500, 420)
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 22)
        root.setSpacing(16)
        heading = QHBoxLayout()
        heading.addWidget(label(t("Movie details" if movie else "Add a movie"), "title"))
        heading.addStretch()
        self.id_label = label(f"ID  #{movie['id']}" if movie else t("ID assigned on save"), "subtitle")
        heading.addWidget(self.id_label)
        root.addLayout(heading)
        self.tabs = QTabWidget()
        root.addWidget(self.tabs, 1)

        details = QWidget()
        form = QFormLayout(details)
        form.setContentsMargins(2, 18, 2, 0)
        form.setVerticalSpacing(16)
        self.title = QLineEdit(str(self.movie.get("title", "")))
        self.title.setPlaceholderText(t("The name of your next favorite film"))
        form.addRow(t("Title"), self.title)
        self.year = QSpinBox()
        self.year.setRange(1888, 2100)
        self.year.setValue(int(self.movie.get("year", QDate.currentDate().year())))
        form.addRow(t("Release year"), self.year)
        self.status = QComboBox()
        self.status.addItem(t("Want to watch"), "watchlist")
        self.status.addItem(t("Watched"), "watched")
        self.status.setCurrentIndex(1 if self.movie.get("status") == "watched" else 0)
        form.addRow(t("Collection"), self.status)
        self.favorite = QCheckBox(t("Keep in Favorites"))
        self.favorite.setChecked(bool(self.movie.get("favorite")))
        form.addRow("", self.favorite)
        self.description = QTextEdit()
        self.description.setAcceptRichText(False)
        self.description.setPlaceholderText(t("What is this film about? Add a synopsis or your own notes."))
        self.description.setPlainText(self.movie.get("description", ""))
        form.addRow(t("Description"), self.description)
        self.tabs.addTab(details, t("Overview"))

        review = QWidget()
        review_layout = QVBoxLayout(review)
        review_layout.setContentsMargins(2, 18, 2, 0)
        review_layout.setSpacing(14)
        review_layout.addWidget(label(t("Movie Review"), "section"))
        review_layout.addWidget(label(t("Give it a score and your opinion."), "subtitle"))
        row = QHBoxLayout()
        row.addWidget(label(t("Your rating")))
        self.rating = QSpinBox()
        self.rating.setRange(0, 10)
        self.rating.setSpecialValueText(t("Not rated"))
        self.rating.setSuffix(" / 10")
        self.rating.setValue(int(self.movie.get("rating", 0)))
        row.addWidget(self.rating)
        row.addStretch()
        review_layout.addLayout(row)
        self.review = QTextEdit()
        self.review.setAcceptRichText(False)
        self.review.setPlaceholderText(t("Your personal review. What worked? How did it make you feel? Would you watch it again?"))
        self.review.setPlainText(self.movie.get("review", ""))
        review_layout.addWidget(self.review, 1)
        self.tabs.addTab(review, t("My review"))

        organization = QWidget()
        organize = QVBoxLayout(organization)
        organize.setContentsMargins(2, 18, 2, 0)
        organize.setSpacing(16)
        organize_form = QFormLayout()
        self.genres = QLineEdit(", ".join(self.movie.get("genres", [])))
        self.genres.setPlaceholderText(t("Separate names with commas"))
        organize_form.addRow(t("Genres"), self.genres)
        self.tags = QLineEdit(", ".join(self.movie.get("tags", [])))
        self.tags.setPlaceholderText(t("Separate names with commas"))
        organize_form.addRow(t("Tags"), self.tags)
        organize.addLayout(organize_form)
        organize.addWidget(label(t("Choose collections for this movie"), "section"))
        self.collection_checks = {}
        for collection in self.available_collections:
            checkbox = QCheckBox(collection["name"])
            checkbox.setChecked(collection["id"] in self.movie.get("collections", []))
            organize.addWidget(checkbox)
            self.collection_checks[collection["id"]] = checkbox
        organize.addStretch()
        organization_scroll = QScrollArea()
        organization_scroll.setWidgetResizable(True)
        organization_scroll.setWidget(organization)
        self.tabs.addTab(organization_scroll, t("Organization"))

        artwork = QWidget()
        artwork_layout = QVBoxLayout(artwork)
        art = QHBoxLayout()
        art.setContentsMargins(2, 18, 2, 0)
        art.setSpacing(26)
        self.poster = PosterView(store.poster_path(self.movie), self.movie.get("poster_crop"), editable=True)
        self.poster.setFixedSize(230, 345)
        self.poster.imageDropped.connect(self.load_poster)
        art.addWidget(self.poster, alignment=Qt.AlignmentFlag.AlignTop)
        controls = QVBoxLayout()
        controls.setSpacing(12)
        controls.addWidget(label(t("Poster position"), "section"))
        hint = label(t("Drag the poster to reposition it.\nAdjust the scale to frame your favorite detail."), "subtitle")
        hint.setWordWrap(True)
        controls.addWidget(hint)
        choose = QPushButton(t("Choose poster…"))
        choose.clicked.connect(self.choose_poster)
        controls.addWidget(choose)
        self.mode = QComboBox()
        self.mode.addItem(t("Fill the frame"), "fill")
        self.mode.addItem(t("Show full image"), "fit")
        self.mode.setCurrentIndex(1 if self.poster.crop["mode"] == "fit" else 0)
        self.mode.currentIndexChanged.connect(self.change_crop)
        controls.addWidget(self.mode)
        self.sliders = {}
        for name, minimum, maximum, title in (("zoom", 100, 300, "Scale"), ("x", -100, 100, "Horizontal position"), ("y", -100, 100, "Vertical position")):
            controls.addWidget(label(t(title), "subtitle"))
            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setRange(minimum, maximum)
            slider.setValue(round(self.poster.crop[name]*100))
            self.sliders[name] = slider
            slider.valueChanged.connect(self.change_crop)
            controls.addWidget(slider)
        self.poster.changed.connect(self.sync_sliders)
        reset = QPushButton(t("Reset framing"))
        reset.clicked.connect(self.reset_crop)
        controls.addWidget(reset)
        remove = QPushButton(t("Remove poster"))
        remove.setObjectName("danger")
        remove.clicked.connect(self.clear_poster)
        controls.addWidget(remove)
        controls.addStretch()
        art.addLayout(controls, 1)
        artwork_layout.addLayout(art)
        artwork_layout.addWidget(label(t("Preview at card sizes"), "section"))
        preview_row = QHBoxLayout()
        self.previews = []
        for caption, size in (("Small", 135), ("Medium", 180), ("Large", 225)):
            column = QVBoxLayout()
            preview = PosterView(store.poster_path(self.movie), self.movie.get("poster_crop"))
            preview.setFixedSize(size, round(size * 1.5))
            column.addWidget(preview)
            column.addWidget(label(t(caption), "subtitle"))
            preview_row.addLayout(column)
            self.previews.append(preview)
        preview_row.addStretch()
        artwork_layout.addLayout(preview_row)
        artwork_scroll = QScrollArea()
        artwork_scroll.setWidgetResizable(True)
        artwork.setMinimumWidth(580)
        artwork_scroll.setWidget(artwork)
        self.tabs.addTab(artwork_scroll, t("Poster studio"))

        footer = QHBoxLayout()
        self.save_status = label("", "subtitle")
        footer.addWidget(self.save_status)
        footer.addStretch()
        cancel = QPushButton(t("Cancel"))
        cancel.clicked.connect(self.reject)
        footer.addWidget(cancel)
        apply = QPushButton(t("Save"))
        apply.clicked.connect(lambda: self.save(close=False))
        footer.addWidget(apply)
        save = QPushButton(t("Save & view"))
        save.setObjectName("primary")
        save.setDefault(True)
        save.clicked.connect(lambda: self.save(close=True))
        footer.addWidget(save)
        root.addLayout(footer)
        QShortcut(QKeySequence.StandardKey.Save, self, activated=lambda: self.save(close=False))
        self.initial = self.snapshot()

    def fields(self):
        return {"title": self.title.text(), "year": self.year.value(),
                "description": self.description.toPlainText(), "review": self.review.toPlainText(),
                "rating": self.rating.value(), "status": self.status.currentData(),
                "favorite": self.favorite.isChecked(), "poster_crop": dict(self.poster.crop),
                "genres": split_labels(self.genres.text()), "tags": split_labels(self.tags.text()),
                "collections": [collection_id for collection_id, checkbox in self.collection_checks.items() if checkbox.isChecked()]}

    def snapshot(self):
        return json.dumps((self.fields(), self.poster_source, self.remove_poster), sort_keys=True)

    def change_crop(self):
        self.poster.crop.update({key: slider.value()/100 for key, slider in self.sliders.items()})
        self.poster.crop["mode"] = self.mode.currentData()
        self.poster.update()
        self.refresh_previews()

    def sync_sliders(self):
        for key, slider in self.sliders.items():
            slider.blockSignals(True)
            slider.setValue(round(self.poster.crop[key]*100))
            slider.blockSignals(False)
        self.refresh_previews()

    def refresh_previews(self):
        source = self.poster.source[0] if self.poster.source else None
        for preview in self.previews:
            preview.set_image(source, dict(self.poster.crop))

    def reset_crop(self):
        self.poster.crop = {"zoom": 1.0, "x": 0.0, "y": 0.0, "mode": "fill"}
        self.sync_sliders()
        self.mode.setCurrentIndex(0)
        self.poster.update()
        self.refresh_previews()

    def choose_poster(self):
        path, _ = QFileDialog.getOpenFileName(self, t("Choose poster…"), "", "Images (*.jpg *.jpeg *.png *.webp *.bmp)")
        if not path:
            return
        self.load_poster(path)

    def load_poster(self, path):
        if not QImageReader(path).canRead():
            QMessageBox.warning(self, t("Cannot open image"), t("Choose a valid image file."))
            return
        previous_path = self.poster.source[0] if self.poster.source else None
        previous_crop = dict(self.poster.crop)
        self.poster.set_image(path)
        if self.poster.pixmap.isNull():
            self.poster.set_image(previous_path, previous_crop)
            QMessageBox.warning(self, t("Cannot open image"), t("This image could not be decoded."))
            return
        self.poster_source = path
        self.remove_poster = False
        self.reset_crop()

    def clear_poster(self):
        self.poster_source = None
        self.remove_poster = True
        self.poster.set_image(None)
        self.reset_crop()

    def save(self, close=True):
        try:
            self.saved_movie = store.save_movie(self.fields(), self.movie.get("id"), self.poster_source, self.remove_poster)
        except (ValueError, OSError) as error:
            QMessageBox.warning(self, t("Could not save"), t(str(error)))
            return
        self.movie = self.saved_movie
        self.id_label.setText(f"ID  #{self.movie['id']}")
        self.poster_source = None
        self.remove_poster = False
        self.poster.set_image(store.poster_path(self.movie))
        self.refresh_previews()
        self.initial = self.snapshot()
        self.save_status.setText(t("Saved"))
        if self.parent() and hasattr(self.parent(), "reload"):
            self.parent().reload()
        if close:
            self.view_after_save = True
            self.accept()

    def showEvent(self, event):
        super().showEvent(event)
        fade_in(self)

    def reject(self):
        if self.snapshot() != self.initial:
            choice = QMessageBox.question(self, t("Unsaved changes"), t("Save your changes before closing?"),
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Save)
            if choice == QMessageBox.StandardButton.Save:
                self.save()
                return
            if choice == QMessageBox.StandardButton.Cancel:
                return
        super().reject()
