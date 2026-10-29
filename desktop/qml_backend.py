import copy
import json
import os
import tempfile
import zipfile
from datetime import date
from pathlib import Path
from PySide6.QtCore import QAbstractListModel, QModelIndex, QObject, Property, Qt, QUrl, Signal, Slot
from PySide6.QtGui import QImageReader, QFontDatabase, QFont, QKeySequence, QColor
from PySide6.QtWidgets import QFileDialog, QColorDialog, QApplication
import keyboard
import movie_store as store
import preferences
from insights import build_insights
from i18n import film_count, set_language, t
from tmdb_service import TmdbService

def split_names(value):
    names = {}
    for part in value.split(","):
        name = part.strip()
        if name:
            names.setdefault(name.casefold(), name)
    return list(names.values())

class MovieModel(QAbstractListModel):
    FilmRole = Qt.ItemDataRole.UserRole + 1

    def __init__(self, parent=None):
        super().__init__(parent)
        self.items = []

    def roleNames(self):
        return {self.FilmRole: b"film"}

    def rowCount(self, parent=QModelIndex()):
        return 0 if parent.isValid() else len(self.items)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if index.isValid() and 0 <= index.row() < len(self.items) and role == self.FilmRole:
            return self.items[index.row()]
        return None

    def replace(self, movies):
        self.beginResetModel()
        self.items = movies
        self.endResetModel()

class ShelfBackend(QObject):
    stateChanged = Signal()
    draftChanged = Signal()
    detailChanged = Signal()
    editorRequested = Signal()
    previewRequested = Signal()
    movieSaved = Signal(bool)
    errorOccurred = Signal(str)
    notified = Signal(str)
    restartRequired = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.model = MovieModel(self)
        self.movies = []
        self._draft = {}
        self._detail = {}
        self._initial = ""
        self._poster_source = None
        self._temporary_poster = None
        self._remove_poster = False
        self.startup_errors = []
        try:
            settings = preferences.load()
        except (ValueError, OSError) as error:
            settings = dict(preferences.DEFAULTS)
            self.startup_errors.append(str(error))
        set_language(settings["language"])
        self._state = {"preferences": settings, "view": "Library", "query": "", "sort": 0,
                       "filters": {}, "collections": [], "genres": [], "tags": [],
                       "total": 0, "watched": 0, "average": "—", "resultCount": 0,
                       "resultLabel": "", "title": t("Library"), "filterCount": 0}
        self.tmdb_service = TmdbService(self)
        if self.tmdb_service.credential_error:
            self.startup_errors.append(self.tmdb_service.credential_error)
        self.tmdb_service.imported.connect(self.importFromTmdb)
        self.tmdb_service.errorOccurred.connect(self.errorOccurred)
        self.reload(startup=True)

    @Property(QObject, constant=True)
    def movieModel(self):
        return self.model

    @Slot(str, result="QVariantMap")
    def collectionInsights(self, collection_id):
        return build_insights(self.movies, collection_id)

    @Property("QStringList", constant=True)
    def fontFamilies(self):
        return sorted(QFontDatabase.families(), key=str.casefold)

    @Property("QVariantList", constant=True)
    def keyboardActions(self):
        return keyboard.ACTIONS

    @Slot(int, int, result=str)
    def keySequence(self, key, modifiers):
        if key in (Qt.Key.Key_Control, Qt.Key.Key_Shift, Qt.Key.Key_Alt, Qt.Key.Key_Meta):
            return ""
        return QKeySequence(key | modifiers).toString(QKeySequence.SequenceFormat.PortableText)

    @Slot("QVariantMap", result=str)
    def shortcutError(self, values):
        try:
            keyboard.validate(values)
        except ValueError as error:
            return t(str(error))
        return ""

    @Slot(str, result="QVariantMap")
    def themePreset(self, name):
        mode = "light" if name == "light" else "dark"
        colors = dict(preferences.PALETTES[mode])
        if name == "contrast":
            colors.update(background="#000000", sidebar="#080808", surface="#101010", elevated="#202020", text="#ffffff", secondary="#e0e0e0", line="#a0a0a0", accent="#69b5ff", onAccent="#000000")
        return {"theme": mode, "theme_style": name, "colors": colors, "theme_name": ""}

    @Slot("QVariantMap", result=str)
    def themeError(self, values):
        try:
            preferences.theme_document(values)
        except (TypeError, ValueError) as error:
            return t(str(error))
        return ""

    @Slot(str, result=str)
    def chooseThemeColor(self, current):
        color = QColorDialog.getColor(QColor(current), None, t("Choose color"))
        return color.name() if color.isValid() else current

    @Slot(result="QVariantMap")
    def importTheme(self):
        filename, _ = QFileDialog.getOpenFileName(None, t("Import theme"), "", "MovieShelf theme (*.json)")
        if not filename:
            return {}
        try:
            return preferences.read_theme(Path(filename))
        except (OSError, UnicodeError, ValueError) as error:
            self.errorOccurred.emit(t(str(error)))
            return {}

    @Slot("QVariantMap")
    def exportTheme(self, values):
        try:
            document = preferences.theme_document(values)
            filename, _ = QFileDialog.getSaveFileName(None, t("Export theme"), "MovieShelf-theme.json", "MovieShelf theme (*.json)")
            if filename:
                target = Path(filename).resolve()
                protected = {Path(value).resolve() for value in (store.MOVIES_FILE, store.COLLECTIONS_FILE, store.COUNTER_FILE, store.LOCK_FILE, store.BASE_DIR / "settings.json")}
                if target in protected:
                    raise ValueError("Choose a theme file outside the library files.")
                store._atomic_write(target, json.dumps(document, ensure_ascii=False, indent=2) + "\n")
        except (OSError, ValueError) as error:
            self.errorOccurred.emit(t(str(error)))

    @Property(QObject, constant=True)
    def tmdb(self):
        return self.tmdb_service

    @Property("QVariantMap", notify=stateChanged)
    def state(self):
        return self._state

    @Property("QVariantMap", notify=draftChanged)
    def draft(self):
        return self._draft

    @Property("QVariantMap", notify=detailChanged)
    def detail(self):
        return self._detail

    @Property(bool, notify=draftChanged)
    def dirty(self):
        return bool(self._draft) and self._snapshot() != self._initial

    @Slot(str, result=str)
    def trText(self, key):
        return t(key)

    def present(self, movie):
        result = {"description": "", "review": "", "rating": 0, "status": "watchlist", "watch_dates": [],
                  "favorite": False, "genres": [], "tags": [], "collections": [], "tmdb_id": 0,
                  "poster_crop": {"zoom": 1.0, "x": 0.0, "y": 0.0, "mode": "fill"}}
        result.update(copy.deepcopy(movie))
        path = store.poster_path(movie)
        result["posterUrl"] = QUrl.fromLocalFile(str(path)).toString() if path else ""
        result["genresText"] = ", ".join(result["genres"])
        result["tagsText"] = ", ".join(result["tags"])
        return result

    def reload(self, startup=False):
        try:
            movies = store.load_movies()
            collections = store.load_collections()
        except (ValueError, OSError) as error:
            if startup:
                self.startup_errors.append(str(error))
            else:
                self.errorOccurred.emit(str(error))
            return False
        self.movies = movies
        self._state["collections"] = collections
        if self._state["view"].startswith("collection:"):
            if self._state["view"][11:] not in {item["id"] for item in collections}:
                self._state["view"] = "Library"
        self._state["total"] = len(movies)
        self._state["watched"] = sum(m.get("status") == "watched" for m in movies)
        ratings = [m["rating"] for m in movies if m.get("rating")]
        self._state["average"] = f"{sum(ratings) / len(ratings):.1f}" if ratings else "—"
        for field in ("genres", "tags"):
            names = {value.casefold(): value for movie in reversed(movies) for value in movie.get(field, [])}
            self._state[field] = sorted(names.values(), key=str.casefold)
        filters = self._state["filters"]
        for key, options in (("genre", self._state["genres"]), ("tag", self._state["tags"]),
                             ("collection", [item["id"] for item in collections])):
            if filters.get(key) and filters[key] not in options:
                filters.pop(key)
        self.refresh()
        return True

    def refresh(self):
        state = self._state
        view, filters = state["view"], state["filters"]
        query = state["query"].strip().casefold()
        results = []
        for movie in self.movies:
            status = movie.get("status", "watchlist")
            rating = movie.get("rating", 0)
            if view == "Watchlist" and status != "watchlist":
                continue
            if view == "Watched" and status != "watched":
                continue
            if view == "Favorites" and not movie.get("favorite"):
                continue
            if view == "My reviews" and not (movie.get("review", "").strip() or rating):
                continue
            if view.startswith("collection:") and view[11:] not in movie.get("collections", []):
                continue
            if filters.get("yearFrom", 0) and movie["year"] < filters["yearFrom"]:
                continue
            if filters.get("yearTo", 0) and movie["year"] > filters["yearTo"]:
                continue
            if (filters.get("ratingFrom", 0) or filters.get("ratingTo", 0)) and not rating:
                continue
            if filters.get("ratingFrom", 0) and rating < filters["ratingFrom"]:
                continue
            if filters.get("ratingTo", 0) and rating > filters["ratingTo"]:
                continue
            if filters.get("status") and status != filters["status"]:
                continue
            if filters.get("favorite") == "yes" and not movie.get("favorite"):
                continue
            if filters.get("favorite") == "no" and movie.get("favorite"):
                continue
            if any(filters.get(key) and filters[key].casefold() not in {v.casefold() for v in movie.get(field, [])}
                   for key, field in (("genre", "genres"), ("tag", "tags"), ("collection", "collections"))):
                continue
            searchable = " ".join(str(movie.get(key, "")) for key in ("title", "id", "year", "description", "review"))
            searchable += " " + " ".join(movie.get("genres", []) + movie.get("tags", []))
            if query not in searchable.casefold():
                continue
            results.append(movie)
        keys = (lambda m: -m["id"], lambda m: m["title"].casefold(),
                lambda m: (-m.get("rating", 0), m["title"].casefold()), lambda m: -m["year"])
        results.sort(key=keys[state["sort"]])
        self.model.replace([self.present(movie) for movie in results])
        state["resultCount"] = len(results)
        state["resultLabel"] = film_count(len(results))
        state["filterCount"] = sum(bool(value) for value in filters.values())
        state["title"] = next((c["name"] for c in state["collections"] if view == "collection:" + c["id"]), t(view))
        self.stateChanged.emit()

    @Slot(str)
    def setView(self, view):
        self._state["view"] = view
        self.refresh()

    @Slot(str)
    def setQuery(self, query):
        if self._state["query"] != query:
            self._state["query"] = query
            self.refresh()

    @Slot(int)
    def setSort(self, index):
        self._state["sort"] = max(0, min(3, index))
        self.refresh()

    @Slot(str, "QVariant")
    def setFilter(self, key, value):
        if key in ("yearFrom", "yearTo", "ratingFrom", "ratingTo"):
            value = int(value or 0)
        self._state["filters"][key] = value
        self.refresh()

    @Slot()
    def resetFilters(self):
        self._state["filters"] = {}
        self.refresh()

    @Slot(int)
    def previewMovie(self, movie_id):
        movie = store.find_movie(self.movies, movie_id)
        if movie:
            self._detail = self.present(movie)
            self.detailChanged.emit()
            self.previewRequested.emit()

    @Slot(int)
    def editMovie(self, movie_id=0):
        movie = store.find_movie(self.movies, movie_id) if movie_id else None
        if movie_id and movie is None:
            self.errorOccurred.emit(t("This movie no longer exists."))
            return
        self._clear_temporary_poster()
        self._draft = self.present(movie or {"id": 0, "title": "", "year": date.today().year})
        known = {c["id"] for c in self._state["collections"]}
        self._draft["collections"] = [v for v in self._draft["collections"] if v in known]
        self._poster_source = None
        self._remove_poster = False
        self._initial = self._snapshot()
        self.draftChanged.emit()
        self.editorRequested.emit()

    def _clear_temporary_poster(self):
        if self._temporary_poster:
            try:
                Path(self._temporary_poster).unlink(missing_ok=True)
            except OSError:
                pass
            self._temporary_poster = None

    @Slot()
    def discardDraft(self):
        self._clear_temporary_poster()

    @Slot("QVariantMap", str)
    def importFromTmdb(self, details, poster):
        self.editMovie(0)
        self._draft.update({"title": details["title"], "year": details["year"] or "",
                            "description": details["description"], "genres": details["genres"],
                            "genresText": ", ".join(details["genres"]), "tmdb_id": details["tmdb_id"]})
        if poster:
            self._temporary_poster = poster
            self._poster_source = poster
            self._draft["posterUrl"] = QUrl.fromLocalFile(poster).toString()
        self.draftChanged.emit()

    def _snapshot(self):
        return json.dumps((self._draft, self._poster_source, self._remove_poster), sort_keys=True)

    @Slot(str, "QVariant")
    def updateDraft(self, key, value):
        if key not in ("title", "year", "description", "review", "rating", "status", "favorite", "genresText", "tagsText"):
            return
        if key == "status" and value == "watchlist" and self._draft.get("watch_dates"):
            self.errorOccurred.emit(t("Remove viewing dates before moving this movie to Watchlist."))
            return
        if self._draft.get(key) != value:
            self._draft[key] = value
            self.draftChanged.emit()

    @Slot(result=str)
    def todayText(self):
        return date.today().isoformat()

    @Slot(str, result=bool)
    def addWatchDate(self, value):
        value = value.strip()
        try:
            if len(value) != 10 or date.fromisoformat(value).isoformat() != value or date.fromisoformat(value) > date.today():
                raise ValueError()
        except ValueError:
            self.errorOccurred.emit(t("Enter a valid viewing date in YYYY-MM-DD format, no later than today."))
            return False
        dates = list(self._draft.get("watch_dates", []))
        dates.append(value)
        dates.sort()
        self._draft["watch_dates"] = dates
        self._draft["status"] = "watched"
        self.draftChanged.emit()
        return True

    @Slot(int)
    def removeWatchDate(self, index):
        dates = list(self._draft.get("watch_dates", []))
        if 0 <= index < len(dates):
            dates.pop(index)
            self._draft["watch_dates"] = dates
            self.draftChanged.emit()

    @Slot(str, bool)
    def selectCollection(self, collection_id, checked):
        values = list(self._draft.get("collections", []))
        if checked and collection_id not in values:
            values.append(collection_id)
        elif not checked and collection_id in values:
            values.remove(collection_id)
        self._draft["collections"] = values
        self.draftChanged.emit()

    @Slot(str, float)
    def setCrop(self, key, value):
        if key not in ("zoom", "x", "y"):
            return
        low, high = (1, 3) if key == "zoom" else (-1, 1)
        self._draft["poster_crop"][key] = max(low, min(high, value))
        self.draftChanged.emit()

    @Slot(str)
    def setCropMode(self, mode):
        if mode in ("fill", "fit"):
            self._draft["poster_crop"]["mode"] = mode
            self.draftChanged.emit()

    @Slot()
    def resetCrop(self):
        self._draft["poster_crop"] = {"zoom": 1.0, "x": 0.0, "y": 0.0, "mode": "fill"}
        self.draftChanged.emit()

    @Slot()
    def choosePoster(self):
        filename, _ = QFileDialog.getOpenFileName(None, t("Choose poster…"), "", "Images (*.jpg *.jpeg *.png *.webp *.bmp)")
        if filename:
            self.loadPoster(filename)

    @Slot(str, result=bool)
    def loadPoster(self, source):
        url = QUrl(source)
        filename = url.toLocalFile() if url.isLocalFile() else source
        path = Path(filename)
        reader = QImageReader(str(path))
        reader.setAutoTransform(True)
        if not path.is_file() or not reader.canRead():
            self.errorOccurred.emit(t("Choose a valid image file."))
            return False
        reader.setScaledSize(reader.size().scaled(2048, 2048, Qt.AspectRatioMode.KeepAspectRatio))
        if reader.read().isNull():
            self.errorOccurred.emit(t("This image could not be decoded."))
            return False
        self._clear_temporary_poster()
        self._poster_source = str(path.resolve())
        self._remove_poster = False
        self._draft["posterUrl"] = QUrl.fromLocalFile(self._poster_source).toString()
        self.resetCrop()
        return True

    @Slot()
    def removePoster(self):
        self._clear_temporary_poster()
        self._poster_source = None
        self._remove_poster = True
        self._draft["posterUrl"] = ""
        self.resetCrop()

    @Slot(bool, result=bool)
    def saveMovie(self, view_after):
        fields = {key: self._draft[key] for key in ("title", "year", "description", "review", "rating", "status", "favorite", "poster_crop", "collections", "watch_dates")}
        fields["genres"] = split_names(self._draft["genresText"])
        fields["tags"] = split_names(self._draft["tagsText"])
        if self._draft.get("tmdb_id"):
            fields["tmdb_id"] = self._draft["tmdb_id"]
        try:
            movie = store.save_movie(fields, self._draft["id"] or None, self._poster_source, self._remove_poster)
        except (OSError, ValueError) as error:
            self.errorOccurred.emit(t(str(error)))
            return False
        self._clear_temporary_poster()
        self._draft = self.present(movie)
        self._poster_source = None
        self._remove_poster = False
        self._initial = self._snapshot()
        self.draftChanged.emit()
        self.reload()
        self._detail = self.present(movie)
        self.detailChanged.emit()
        self.movieSaved.emit(view_after)
        self.notified.emit(t("Changes saved."))
        return True

    @Slot(int, result=bool)
    def deleteMovie(self, movie_id):
        try:
            store.delete_movie(movie_id)
        except (OSError, ValueError) as error:
            self.errorOccurred.emit(t(str(error)))
            return False
        self.reload()
        return True

    @Slot(str, str, result=bool)
    def saveCollection(self, collection_id, name):
        try:
            if collection_id:
                store.rename_collection(collection_id, name)
            else:
                store.create_collection(name)
        except (OSError, ValueError) as error:
            self.errorOccurred.emit(t(str(error)))
            return False
        self.reload()
        return True

    @Slot(str, result=bool)
    def deleteCollection(self, collection_id):
        try:
            store.delete_collection(collection_id)
        except (OSError, ValueError) as error:
            self.errorOccurred.emit(t(str(error)))
            return False
        self.reload()
        return True

    @Slot("QVariantMap", result=bool)
    def saveSettings(self, values):
        previous = self._state["preferences"]
        result = dict(self._state["preferences"])
        result.update(values)
        try:
            result = preferences.validate(result)
            preferences.save(result)
        except (OSError, ValueError) as error:
            self.errorOccurred.emit(t(str(error)))
            return False
        self._state["preferences"] = result
        app = QApplication.instance()
        if app is not None:
            font = QFont(result["font_family"] or "Medeo Sans")
            font.setPixelSize(round(14 * result["text_scale"]))
            app.setFont(font)
        set_language(result["language"])
        self.refresh()
        self.notified.emit(t("Settings saved."))
        if any(result[key] != previous[key] for key in ("font_family", "ui_scale")):
            self.restartRequired.emit()
        return True

    @Slot(int)
    def saveCardSize(self, size):
        if size != self._state["preferences"]["card_size"]:
            self.saveSettings({"card_size": size})

    @Slot()
    def exportBackup(self):
        filename, _ = QFileDialog.getSaveFileName(None, t("Export backup"), "MovieShelf-backup.zip", "ZIP archive (*.zip)")
        if filename:
            self.writeBackup(filename)

    def writeBackup(self, filename):
        temporary = None
        try:
            target = Path(filename).resolve()
            if target in (store.MOVIES_FILE, store.COUNTER_FILE, store.COLLECTIONS_FILE, store.LOCK_FILE, store.BASE_DIR / "settings.json") or store.POSTERS_DIR.resolve() in target.parents:
                raise ValueError(t("Choose a backup location outside the library files."))
            descriptor, name = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=target.parent)
            os.close(descriptor)
            temporary = Path(name)
            with store._collection_lock():
                movies = store.load_movies()
                collections = store.load_collections()
                with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED) as archive:
                    archive.writestr("movies.json", json.dumps(movies, ensure_ascii=False, indent=2))
                    archive.writestr("collections.json", json.dumps(collections, ensure_ascii=False, indent=2))
                    if store.COUNTER_FILE.is_file():
                        archive.write(store.COUNTER_FILE, store.COUNTER_FILE.name)
                    for path in {store.poster_path(movie) for movie in movies} - {None}:
                        archive.write(path, path.relative_to(store.BASE_DIR).as_posix())
            os.replace(temporary, target)
        except (OSError, ValueError) as error:
            self.errorOccurred.emit(str(error))
            return False
        finally:
            if temporary:
                temporary.unlink(missing_ok=True)
        self.notified.emit(t("Your films, reviews and posters have been exported."))
        return True
