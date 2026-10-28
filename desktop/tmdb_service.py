import json
import os
import re
import tempfile
from pathlib import Path
from PySide6.QtCore import QObject, Property, QStandardPaths, QUrl, QUrlQuery, Signal, Slot
from PySide6.QtGui import QImage
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest
from i18n import t

API_ROOT = "https://api.themoviedb.org/3"
IMAGE_ROOT = "https://image.tmdb.org/t/p"
POSTER_PATH = re.compile(r"^/[A-Za-z0-9_-]+\.(?:jpg|jpeg|png|webp)$", re.IGNORECASE)

def credential_path():
    directory = Path(QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppConfigLocation))
    return directory / "tmdb.json"

def poster_url(path, size="w500"):
    return f"{IMAGE_ROOT}/{size}{path}" if isinstance(path, str) and POSTER_PATH.fullmatch(path) else ""

def movie_fields(details):
    if not isinstance(details, dict) or type(details.get("id")) is not int or details["id"] < 1:
        raise ValueError(t("TMDB returned invalid movie details."))
    title = details.get("title") or details.get("original_title")
    if not isinstance(title, str) or not title.strip():
        raise ValueError(t("TMDB returned invalid movie details."))
    release_date = details.get("release_date") or ""
    try:
        year = int(release_date[:4])
    except (TypeError, ValueError):
        year = 0
    if not 1888 <= year <= 2100:
        year = 0
    genres = []
    for item in details.get("genres", []):
        if isinstance(item, dict) and isinstance(item.get("name"), str) and item["name"].strip():
            name = item["name"].strip()
            if name.casefold() not in {value.casefold() for value in genres}:
                genres.append(name)
    return {"tmdb_id": details["id"], "title": title.strip(), "year": year,
            "description": details.get("overview") if isinstance(details.get("overview"), str) else "",
            "genres": genres, "poster_path": details.get("poster_path")}

class TmdbService(QObject):
    stateChanged = Signal()
    imported = Signal("QVariantMap", str)
    errorOccurred = Signal(str)

    def __init__(self, parent=None, manager=None):
        super().__init__(parent)
        self.manager = manager or QNetworkAccessManager(self)
        self._key = ""
        self.credential_error = ""
        self._state = {"hasKey": False, "searching": False, "importing": False,
                       "results": [], "query": "", "error": ""}
        self._search_reply = None
        self._import_reply = None
        self._generation = 0
        self.loadCredential()

    @Property("QVariantMap", notify=stateChanged)
    def state(self):
        return self._state

    def loadCredential(self):
        try:
            data = json.loads(credential_path().read_text(encoding="utf-8"))
            if not isinstance(data, dict) or not isinstance(data.get("credential"), str):
                raise ValueError("Invalid TMDB credential file.")
            self._key = data["credential"].strip()
        except FileNotFoundError:
            self._key = ""
        except (OSError, UnicodeError, ValueError):
            self._key = ""
            self.credential_error = t("Could not read your local TMDB key.")
        self._state["hasKey"] = bool(self._key)
        self.stateChanged.emit()

    @Slot(str, result=bool)
    def saveCredential(self, value):
        value = value.strip()
        if value.lower().startswith("bearer "):
            value = value[7:].strip()
        if not value or len(value) > 2048 or not value.isascii() or any(character.isspace() or ord(character) < 33 for character in value):
            self.errorOccurred.emit(t("Enter your TMDB API key or Read Access Token."))
            return False
        path = credential_path()
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            descriptor, name = tempfile.mkstemp(prefix=".tmdb.", suffix=".tmp", dir=path.parent)
            temporary = Path(name)
            try:
                with os.fdopen(descriptor, "w", encoding="utf-8") as file:
                    json.dump({"credential": value}, file)
                    file.flush()
                    os.fsync(file.fileno())
                os.chmod(temporary, 0o600)
                os.replace(temporary, path)
            finally:
                temporary.unlink(missing_ok=True)
        except OSError as error:
            self.errorOccurred.emit(t("Could not save your local TMDB key.") + " " + str(error))
            return False
        self._key = value
        self._state["hasKey"] = True
        self.stateChanged.emit()
        return True

    @Slot()
    def clearCredential(self):
        try:
            credential_path().unlink(missing_ok=True)
        except OSError as error:
            self.errorOccurred.emit(t("Could not remove your local TMDB key.") + " " + str(error))
            return
        self._key = ""
        self.cancelSearch()
        self.cancelImport()
        self._state["hasKey"] = False
        self._state["importing"] = False
        self.stateChanged.emit()

    def _request(self, path, parameters=None, image=False):
        url = QUrl(path if image else API_ROOT + path)
        if not image:
            query = QUrlQuery()
            for name, value in (parameters or {}).items():
                query.addQueryItem(name, str(value))
            if re.fullmatch(r"[a-fA-F0-9]{32}", self._key):
                query.addQueryItem("api_key", self._key)
            url.setQuery(query)
        request = QNetworkRequest(url)
        request.setRawHeader(b"Accept", b"application/json" if not image else b"image/*")
        if not image and not re.fullmatch(r"[a-fA-F0-9]{32}", self._key):
            request.setRawHeader(b"Authorization", ("Bearer " + self._key).encode("ascii"))
        request.setTransferTimeout(15000)
        request.setAttribute(QNetworkRequest.Attribute.RedirectPolicyAttribute,
                             QNetworkRequest.RedirectPolicy.SameOriginRedirectPolicy)
        return self.manager.get(request)

    def _check(self, reply):
        status = reply.attribute(QNetworkRequest.Attribute.HttpStatusCodeAttribute)
        if status in (401, 403):
            return t("TMDB rejected this key. Check it in Settings.")
        if status == 429:
            return t("TMDB is busy. Please try again later.")
        if status and status >= 400:
            return t("TMDB could not complete the request.")
        if reply.error() != QNetworkReply.NetworkError.NoError:
            return t("Could not reach TMDB. Check your connection.")
        return ""

    @Slot()
    def cancelSearch(self):
        self._generation += 1
        if self._search_reply:
            self._search_reply.abort()
            self._search_reply = None
        self._state["searching"] = False
        self.stateChanged.emit()

    @Slot(str)
    def search(self, text):
        self.cancelSearch()
        query = text.strip()
        self._state["query"] = query
        self._state["results"] = []
        self._state["error"] = ""
        if len(query) < 2:
            self.stateChanged.emit()
            return
        if not self._key:
            self._state["error"] = t("Add your personal TMDB key first.")
            self.stateChanged.emit()
            return
        generation = self._generation
        language = {"en": "en-US", "ru": "ru-RU", "kk": "kk-KZ"}.get(self.parent().state["preferences"]["language"], "en-US")
        reply = self._request("/search/movie", {"query": query, "language": language, "include_adult": "false", "page": 1})
        self._search_reply = reply
        self._state["searching"] = True
        self.stateChanged.emit()
        reply.finished.connect(lambda: self._finish_search(reply, generation))

    def _finish_search(self, reply, generation):
        try:
            if generation != self._generation:
                return
            self._search_reply = None
            self._state["searching"] = False
            error = self._check(reply)
            if error:
                self._state["error"] = error
                return
            payload = json.loads(bytes(reply.readAll()))
            if not isinstance(payload, dict) or not isinstance(payload.get("results"), list):
                raise ValueError()
            results = []
            for item in payload["results"]:
                if not isinstance(item, dict) or type(item.get("id")) is not int:
                    continue
                title = item.get("title") or item.get("original_title")
                if not isinstance(title, str) or not title.strip():
                    continue
                release_date = item.get("release_date") or ""
                results.append({"id": item["id"], "title": title.strip(),
                                "year": release_date[:4] if isinstance(release_date, str) else "",
                                "description": item.get("overview") if isinstance(item.get("overview"), str) else "",
                                "posterUrl": poster_url(item.get("poster_path"), "w342")})
            self._state["results"] = results
        except (UnicodeError, ValueError):
            self._state["error"] = t("TMDB returned an invalid response.")
        finally:
            reply.deleteLater()
            if generation == self._generation:
                self.stateChanged.emit()

    @Slot()
    def cancelImport(self):
        if self._import_reply:
            self._import_reply.abort()
            self._import_reply = None
        self._state["importing"] = False
        self.stateChanged.emit()

    @Slot(int)
    def importMovie(self, movie_id):
        if not self._key or type(movie_id) is not int or movie_id < 1 or self._state["importing"]:
            return
        self._state["importing"] = True
        self._state["error"] = ""
        self.stateChanged.emit()
        language = {"en": "en-US", "ru": "ru-RU", "kk": "kk-KZ"}.get(self.parent().state["preferences"]["language"], "en-US")
        reply = self._request(f"/movie/{movie_id}", {"language": language})
        self._import_reply = reply
        reply.finished.connect(lambda: self._finish_details(reply))

    def _finish_details(self, reply):
        try:
            if reply is not self._import_reply:
                return
            self._import_reply = None
            error = self._check(reply)
            if error:
                self._state["error"] = error
                self._state["importing"] = False
                return
            details = movie_fields(json.loads(bytes(reply.readAll())))
            url = poster_url(details["poster_path"], "w780")
            if not url:
                self._state["importing"] = False
                self.imported.emit(details, "")
                return
            image_reply = self._request(url, image=True)
            self._import_reply = image_reply
            image_reply.finished.connect(lambda: self._finish_poster(image_reply, details))
        except (UnicodeError, ValueError):
            self._state["error"] = t("TMDB returned invalid movie details.")
            self._state["importing"] = False
        finally:
            reply.deleteLater()
            self.stateChanged.emit()

    def _finish_poster(self, reply, details):
        path = ""
        try:
            if reply is not self._import_reply:
                return
            self._import_reply = None
            if self._check(reply):
                self.errorOccurred.emit(t("The TMDB poster could not be downloaded. You can add one manually."))
            else:
                content = bytes(reply.readAll())
                if len(content) > 10_000_000 or QImage.fromData(content).isNull():
                    self.errorOccurred.emit(t("The TMDB poster could not be downloaded. You can add one manually."))
                else:
                    descriptor, path = tempfile.mkstemp(prefix="movieshelf-tmdb-", suffix=Path(details["poster_path"]).suffix.lower())
                    with os.fdopen(descriptor, "wb") as file:
                        file.write(content)
            self.imported.emit(details, path)
        except OSError:
            if path:
                Path(path).unlink(missing_ok=True)
            self.errorOccurred.emit(t("The TMDB poster could not be downloaded. You can add one manually."))
            self.imported.emit(details, "")
        finally:
            self._state["importing"] = False
            self.stateChanged.emit()
            reply.deleteLater()
