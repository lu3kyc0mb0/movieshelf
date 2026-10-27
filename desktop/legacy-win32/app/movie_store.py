import json
import os
import shutil
import sys
import tempfile
import uuid
from contextlib import contextmanager
from pathlib import Path

compiled = globals().get("__compiled__")
if compiled is not None:
    BASE_DIR = Path(compiled.containing_dir).resolve()
elif getattr(sys, "frozen", False):
    BASE_DIR = Path(sys.executable).resolve().parent
else:
    BASE_DIR = Path(__file__).resolve().parent
MOVIES_FILE = BASE_DIR / "movies.json"
POSTERS_DIR = BASE_DIR / "posters"
COUNTER_FILE = BASE_DIR / "movie_id_counter.json"
LOCK_FILE = BASE_DIR / "movies.json.lock"
COLLECTIONS_FILE = BASE_DIR / "collections.json"

def _atomic_write(path, contents):
    descriptor, name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as file:
            file.write(contents)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)

@contextmanager
def _collection_lock():
    with LOCK_FILE.open("a+b") as lock:
        lock.seek(0)
        if os.name == "nt":
            import msvcrt
            msvcrt.locking(lock.fileno(), msvcrt.LK_LOCK, 1)
        else:
            import fcntl
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            lock.seek(0)
            if os.name == "nt":
                msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(lock.fileno(), fcntl.LOCK_UN)

def _validate_movie(movie, index, seen):
    if not isinstance(movie, dict):
        raise ValueError(f"Movie #{index} must be an object.")
    movie_id = movie.get("id")
    if type(movie_id) is not int or movie_id < 1 or movie_id in seen:
        raise ValueError(f"Movie #{index} has an invalid or duplicate ID.")
    seen.add(movie_id)
    if not isinstance(movie.get("title"), str) or not movie["title"].strip():
        raise ValueError(f"Movie #{index} needs a nonempty title.")
    year = movie.get("year")
    if type(year) is not int or not 1888 <= year <= 2100:
        raise ValueError(f"Movie #{index} has an invalid release year.")
    if "rating" in movie and (type(movie["rating"]) is not int or not 0 <= movie["rating"] <= 10):
        raise ValueError(f"Movie #{index} has an invalid rating.")
    for key in ("description", "review", "poster"):
        if key in movie and not isinstance(movie[key], str):
            raise ValueError(f"Movie #{index} has an invalid {key}.")
    if "favorite" in movie and type(movie["favorite"]) is not bool:
        raise ValueError(f"Movie #{index} has an invalid favorite flag.")
    if "status" in movie and movie["status"] not in ("watchlist", "watched"):
        raise ValueError(f"Movie #{index} has an invalid status.")
    if "poster" in movie and ("\0" in movie["poster"] or Path(movie["poster"]).is_absolute()):
        raise ValueError(f"Movie #{index} has an invalid poster path.")
    if "poster_crop" in movie:
        crop = movie["poster_crop"]
        if not isinstance(crop, dict) or crop.get("mode") not in ("fit", "fill"):
            raise ValueError(f"Movie #{index} has invalid poster framing.")
        for key, minimum, maximum in (("zoom", 1, 3), ("x", -1, 1), ("y", -1, 1)):
            value = crop.get(key)
            if type(value) not in (int, float) or not minimum <= value <= maximum:
                raise ValueError(f"Movie #{index} has invalid poster framing.")
    for key in ("genres", "tags", "collections"):
        if key in movie:
            values = movie[key]
            if (not isinstance(values, list) or any(not isinstance(value, str) or not value.strip() for value in values)
                    or len({value.casefold() for value in values}) != len(values)):
                raise ValueError(f"Movie #{index} has invalid {key}.")

def load_movies():
    try:
        with MOVIES_FILE.open("r", encoding="utf-8") as file:
            movies = json.load(file)
    except FileNotFoundError:
        return []
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"Could not read movies.json: {error}") from error
    if not isinstance(movies, list):
        raise ValueError("movies.json must contain a list of movies.")
    seen = set()
    for index, movie in enumerate(movies, 1):
        _validate_movie(movie, index, seen)
    return movies

def save_movies(movies):
    _atomic_write(MOVIES_FILE, json.dumps(movies, ensure_ascii=False, indent=2) + "\n")

def load_collections():
    try:
        collections = json.loads(COLLECTIONS_FILE.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return []
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"Could not read collections.json: {error}") from error
    if not isinstance(collections, list):
        raise ValueError("collections.json must contain a list.")
    ids = set()
    names = set()
    for collection in collections:
        if not isinstance(collection, dict):
            raise ValueError("collections.json contains an invalid collection.")
        collection_id = collection.get("id")
        name = collection.get("name")
        if (not isinstance(collection_id, str) or not collection_id.strip() or collection_id in ids
                or not isinstance(name, str) or not name.strip() or name != name.strip() or len(name) > 60
                or name.casefold() in names):
            raise ValueError("collections.json contains an invalid or duplicate collection.")
        ids.add(collection_id)
        names.add(name.casefold())
    return collections

def _save_collections(collections):
    _atomic_write(COLLECTIONS_FILE, json.dumps(collections, ensure_ascii=False, indent=2) + "\n")

def create_collection(name):
    if not isinstance(name, str):
        raise ValueError("Collection name must be text.")
    name = name.strip()
    if not name or len(name) > 60:
        raise ValueError("Collection names must be between 1 and 60 characters.")
    with _collection_lock():
        collections = load_collections()
        if any(item["name"].casefold() == name.casefold() for item in collections):
            raise ValueError("A collection with this name already exists.")
        collection = {"id": uuid.uuid4().hex, "name": name}
        collections.append(collection)
        _save_collections(collections)
        return collection

def rename_collection(collection_id, name):
    if not isinstance(name, str):
        raise ValueError("Collection name must be text.")
    name = name.strip()
    if not name or len(name) > 60:
        raise ValueError("Collection names must be between 1 and 60 characters.")
    with _collection_lock():
        collections = load_collections()
        target = next((item for item in collections if item["id"] == collection_id), None)
        if target is None:
            raise ValueError("Collection was not found.")
        if any(item["id"] != collection_id and item["name"].casefold() == name.casefold() for item in collections):
            raise ValueError("A collection with this name already exists.")
        target["name"] = name
        _save_collections(collections)
        return target

def delete_collection(collection_id):
    with _collection_lock():
        collections = load_collections()
        remaining = [item for item in collections if item["id"] != collection_id]
        if len(remaining) == len(collections):
            raise ValueError("Collection was not found.")
        _save_collections(remaining)

def _current_id_counter(movies):
    try:
        value = json.loads(COUNTER_FILE.read_text(encoding="utf-8"))
    except FileNotFoundError:
        value = {"last_id": 0}
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"Could not read movie ID counter: {error}") from error
    if not isinstance(value, dict) or type(value.get("last_id")) is not int or value["last_id"] < 0:
        raise ValueError("Movie ID counter is invalid.")
    return max([value["last_id"], *(movie["id"] for movie in movies)])

def _next_id(movies):
    movie_id = _current_id_counter(movies) + 1
    _atomic_write(COUNTER_FILE, json.dumps({"last_id": movie_id}) + "\n")
    return movie_id

def find_movie(movies, movie_id):
    return next((movie for movie in movies if movie["id"] == movie_id), None)

def search_movies(movies, query):
    query = query.strip().casefold()
    if not query:
        return movies
    return [
        movie for movie in movies
        if query in str(movie["title"]).casefold()
        or query in str(movie["year"])
        or query == str(movie["id"])
    ]

def poster_path(movie):
    relative = movie.get("poster")
    if not relative:
        return None
    path = (BASE_DIR / relative).resolve()
    if POSTERS_DIR.resolve() not in path.parents:
        return None
    return path if path.is_file() else None

def copy_poster(source):
    if not source:
        return None
    source = Path(source)
    POSTERS_DIR.mkdir(exist_ok=True)
    destination = POSTERS_DIR / f"{uuid.uuid4().hex}{source.suffix.lower()}"
    descriptor, name = tempfile.mkstemp(prefix=".poster.", suffix=".tmp", dir=POSTERS_DIR)
    os.close(descriptor)
    temporary = Path(name)
    try:
        shutil.copy2(source, temporary)
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)
    return destination.relative_to(BASE_DIR).as_posix()

def _validated_fields(title, year):
    if not isinstance(title, str) or not title.strip():
        raise ValueError("Please enter a movie title.")
    try:
        year = int(year)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError("Please enter a valid release year.") from error
    if not 1888 <= year <= 2100:
        raise ValueError("Please enter a release year between 1888 and 2100.")
    return title.strip(), year

def _remove_unused_poster(relative, movies):
    if not relative or any(movie.get("poster") == relative for movie in movies):
        return
    path = (BASE_DIR / relative).resolve()
    if POSTERS_DIR.resolve() in path.parents:
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass

def add_movie(title, year, poster_source=None):
    title, year = _validated_fields(title, year)
    with _collection_lock():
        movies = load_movies()
        movie = {"id": _next_id(movies), "title": title, "year": year}
        copied = copy_poster(poster_source) if poster_source else None
        if copied:
            movie["poster"] = copied
        movies.append(movie)
        try:
            save_movies(movies)
        except OSError:
            _remove_unused_poster(copied, [])
            raise
        return movie

def update_movie(movie_id, title, year, poster_source=None, remove_poster=False):
    title, year = _validated_fields(title, year)
    with _collection_lock():
        movies = load_movies()
        existing = find_movie(movies, movie_id)
        if existing is None:
            raise ValueError(f"Movie #{movie_id} was not found.")
        movie = dict(existing, title=title, year=year)
        old_poster = movie.get("poster")
        copied = None
        if remove_poster:
            movie.pop("poster", None)
        elif poster_source:
            copied = copy_poster(poster_source)
            movie["poster"] = copied
        movies[movies.index(existing)] = movie
        try:
            save_movies(movies)
        except OSError:
            _remove_unused_poster(copied, [])
            raise
        if remove_poster or copied:
            _remove_unused_poster(old_poster, movies)
        return movie

def delete_movie(movie_id):
    with _collection_lock():
        movies = load_movies()
        movie = find_movie(movies, movie_id)
        if movie is None:
            raise ValueError(f"Movie #{movie_id} was not found.")
        highest = _current_id_counter(movies)
        _atomic_write(COUNTER_FILE, json.dumps({"last_id": highest}) + "\n")
        movies.remove(movie)
        save_movies(movies)
        _remove_unused_poster(movie.get("poster"), movies)
        return movie

def save_movie(fields, movie_id=None, poster_source=None, remove_poster=False):
    title, year = _validated_fields(fields.get("title"), fields.get("year"))
    try:
        rating = int(fields.get("rating", 0))
    except (TypeError, ValueError, OverflowError) as error:
        raise ValueError("Please enter a valid rating.") from error
    if not 0 <= rating <= 10:
        raise ValueError("Check the rating (1–10, or unrated).")
    with _collection_lock():
        movies = load_movies()
        existing = find_movie(movies, movie_id) if movie_id is not None else None
        if movie_id is not None and existing is None:
            raise ValueError("This movie no longer exists.")
        movie = dict(existing) if existing else {"id": _next_id(movies)}
        old_poster = movie.get("poster")
        movie.update({key: fields[key] for key in ("description", "review", "status", "favorite", "poster_crop", "genres", "tags", "collections") if key in fields})
        movie.update(title=title, year=year, rating=rating)
        _validate_movie(movie, 1, set())
        if "collections" in fields:
            known = {item["id"] for item in load_collections()}
            if any(collection_id not in known for collection_id in movie["collections"]):
                raise ValueError("A selected collection no longer exists.")
        copied = None
        if remove_poster:
            movie.pop("poster", None)
        elif poster_source:
            copied = copy_poster(poster_source)
            movie["poster"] = copied
        if existing is not None:
            movies[movies.index(existing)] = movie
        else:
            movies.append(movie)
        try:
            save_movies(movies)
        except OSError:
            _remove_unused_poster(copied, [])
            raise
        if copied or remove_poster:
            _remove_unused_poster(old_poster, movies)
        return movie
