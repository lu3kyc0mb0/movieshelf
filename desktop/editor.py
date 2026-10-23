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
        self.setWindowTitle("Movie details · MovieShelf")
        self.resize(800, 670)
        self.setMinimumSize(500, 420)
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 22)
        root.setSpacing(16)
        heading = QHBoxLayout()
        heading.addWidget(label("Movie details" if movie else "Add a movie", "title"))
        heading.addStretch()
        self.id_label = label(f"ID  #{movie['id']}" if movie else "ID assigned on save", "subtitle")
        heading.addWidget(self.id_label)
        root.addLayout(heading)
        self.tabs = QTabWidget()
        root.addWidget(self.tabs, 1)

        details = QWidget()
        form = QFormLayout(details)
        form.setContentsMargins(2, 18, 2, 0)
        form.setVerticalSpacing(16)
        self.title = QLineEdit(str(self.movie.get("title", "")))
        self.title.setPlaceholderText("The name of your next favorite film")
        form.addRow("Title", self.title)
        self.year = QSpinBox()
        self.year.setRange(1888, 2100)
        self.year.setValue(int(self.movie.get("year", QDate.currentDate().year())))
        form.addRow("Release year", self.year)
        self.status = QComboBox()
        self.status.addItem("Want to watch", "watchlist")
        self.status.addItem("Watched", "watched")
        self.status.setCurrentIndex(1 if self.movie.get("status") == "watched" else 0)
        form.addRow("Collection", self.status)
        self.favorite = QCheckBox("Keep in Favorites")
        self.favorite.setChecked(bool(self.movie.get("favorite")))
        form.addRow("", self.favorite)
        self.description = QTextEdit()
        self.description.setAcceptRichText(False)
        self.description.setPlaceholderText("What is this film about? Add a synopsis or your own notes.")
        self.description.setPlainText(self.movie.get("description", ""))
        form.addRow("Description", self.description)
        self.tabs.addTab(details, "Overview")

        review = QWidget()
        review_layout = QVBoxLayout(review)
        review_layout.setContentsMargins(2, 18, 2, 0)
        review_layout.setSpacing(14)
        review_layout.addWidget(label("Movie Review", "section"))
        review_layout.addWidget(label("Give it a score and your opinion.", "subtitle"))
        row = QHBoxLayout()
        row.addWidget(label("Your rating"))
        self.rating = QSpinBox()
        self.rating.setRange(0, 10)
        self.rating.setSpecialValueText("Not rated")
        self.rating.setSuffix(" / 10")
        self.rating.setValue(int(self.movie.get("rating", 0)))
        row.addWidget(self.rating)
        row.addStretch()
        review_layout.addLayout(row)
        self.review = QTextEdit()
        self.review.setAcceptRichText(False)
        self.review.setPlaceholderText("Your personal review. What worked? How did it make you feel? Would you watch it again?")
        self.review.setPlainText(self.movie.get("review", ""))
        review_layout.addWidget(self.review, 1)
        self.tabs.addTab(review, "My review")

        artwork = QWidget()
        art = QHBoxLayout(artwork)
        art.setContentsMargins(2, 18, 2, 0)
        art.setSpacing(26)
        self.poster = PosterView(store.poster_path(self.movie), self.movie.get("poster_crop"), editable=True)
        self.poster.setFixedSize(230, 345)
        art.addWidget(self.poster, alignment=Qt.AlignmentFlag.AlignTop)
        controls = QVBoxLayout()
        controls.setSpacing(12)
        controls.addWidget(label("Poster position", "section"))
        hint = label("Drag the poster to reposition it.\nAdjust the scale to frame your favorite detail.", "subtitle")
        hint.setWordWrap(True)
        controls.addWidget(hint)
        choose = QPushButton("Choose poster…")
        choose.clicked.connect(self.choose_poster)
        controls.addWidget(choose)
        self.mode = QComboBox()
        self.mode.addItem("Fill the frame", "fill")
        self.mode.addItem("Show full image", "fit")
        self.mode.setCurrentIndex(1 if self.poster.crop["mode"] == "fit" else 0)
        self.mode.currentIndexChanged.connect(self.change_crop)
        controls.addWidget(self.mode)
        self.sliders = {}
        for name, minimum, maximum, title in (("zoom", 100, 300, "Scale"), ("x", -100, 100, "Horizontal position"), ("y", -100, 100, "Vertical position")):
            controls.addWidget(label(title, "subtitle"))
            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setRange(minimum, maximum)
            slider.setValue(round(self.poster.crop[name]*100))
            self.sliders[name] = slider
            slider.valueChanged.connect(self.change_crop)
            controls.addWidget(slider)
        self.poster.changed.connect(self.sync_sliders)
        reset = QPushButton("Reset framing")
        reset.clicked.connect(self.reset_crop)
        controls.addWidget(reset)
        remove = QPushButton("Remove poster")
        remove.setObjectName("danger")
        remove.clicked.connect(self.clear_poster)
        controls.addWidget(remove)
        controls.addStretch()
        art.addLayout(controls, 1)
        artwork_scroll = QScrollArea()
        artwork_scroll.setWidgetResizable(True)
        artwork.setMinimumWidth(580)
        artwork_scroll.setWidget(artwork)
        self.tabs.addTab(artwork_scroll, "Poster studio")

        footer = QHBoxLayout()
        self.save_status = label("", "subtitle")
        footer.addWidget(self.save_status)
        footer.addStretch()
        cancel = QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        footer.addWidget(cancel)
        apply = QPushButton("Save")
        apply.clicked.connect(lambda: self.save(close=False))
        footer.addWidget(apply)
        save = QPushButton("Save & view")
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
                "favorite": self.favorite.isChecked(), "poster_crop": dict(self.poster.crop)}

    def snapshot(self):
        return json.dumps((self.fields(), self.poster_source, self.remove_poster), sort_keys=True)

    def change_crop(self):
        self.poster.crop.update({key: slider.value()/100 for key, slider in self.sliders.items()})
        self.poster.crop["mode"] = self.mode.currentData()
        self.poster.update()

    def sync_sliders(self):
        for key, slider in self.sliders.items():
            slider.blockSignals(True)
            slider.setValue(round(self.poster.crop[key]*100))
            slider.blockSignals(False)

    def reset_crop(self):
        self.poster.crop = {"zoom": 1.0, "x": 0.0, "y": 0.0, "mode": "fill"}
        self.sync_sliders()
        self.mode.setCurrentIndex(0)
        self.poster.update()

    def choose_poster(self):
        path, _ = QFileDialog.getOpenFileName(self, "Choose artwork", "", "Images (*.jpg *.jpeg *.png *.webp *.bmp)")
        if not path:
            return
        if not QImageReader(path).canRead():
            QMessageBox.warning(self, "Cannot open image", "Choose a valid image file.")
            return
        previous_path = self.poster.source[0] if self.poster.source else None
        previous_crop = dict(self.poster.crop)
        self.poster.set_image(path)
        if self.poster.pixmap.isNull():
            self.poster.set_image(previous_path, previous_crop)
            QMessageBox.warning(self, "Cannot open image", "This image could not be decoded.")
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
            QMessageBox.warning(self, "Could not save", str(error))
            return
        self.movie = self.saved_movie
        self.id_label.setText(f"ID  #{self.movie['id']}")
        self.poster_source = None
        self.remove_poster = False
        self.poster.set_image(store.poster_path(self.movie))
        self.initial = self.snapshot()
        self.save_status.setText("Saved")
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
            choice = QMessageBox.question(self, "Unsaved changes", "Save your changes before closing?",
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Save)
            if choice == QMessageBox.StandardButton.Save:
                self.save()
                return
            if choice == QMessageBox.StandardButton.Cancel:
                return
        super().reject()
