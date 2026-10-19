import json
import os
import shutil
import sys
import uuid
from pathlib import Path

BASE_DIR = (
    Path(sys.executable).resolve().parent
    if getattr(sys, "frozen", False) or "__compiled__" in globals()
    else Path(__file__).resolve().parent
)
MOVIES_FILE = BASE_DIR / "movies.json"
POSTERS_DIR = BASE_DIR / "posters"

def load_movies():
    if not MOVIES_FILE.exists():
        return []
    try:
        with MOVIES_FILE.open("r", encoding="utf-8") as file:
            movies = json.load(file)
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError(f"Could not read movies.json: {error}") from error
    if not isinstance(movies, list):
        raise ValueError("movies.json must contain a list of movies.")
    for movie in movies:
        if not isinstance(movie, dict) or not all(key in movie for key in ("id", "title", "year")):
            raise ValueError("Each movie needs an id, title and year.")
    return movies

def save_movies(movies):
    temporary = MOVIES_FILE.with_suffix(".json.tmp")
    try:
        with temporary.open("w", encoding="utf-8") as file:
            json.dump(movies, file, ensure_ascii=False, indent=2)
            file.write("\n")
        os.replace(temporary, MOVIES_FILE)
    except OSError:
        temporary.unlink(missing_ok=True)
        raise

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
    shutil.copy2(source, destination)
    return destination.relative_to(BASE_DIR).as_posix()

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
    movies = load_movies()
    movie_id = max((int(movie["id"]) for movie in movies), default=0) + 1
    movie = {"id": movie_id, "title": title.strip(), "year": int(year)}
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
    movies = load_movies()
    movie = find_movie(movies, movie_id)
    if movie is None:
        raise ValueError(f"Movie #{movie_id} was not found.")
    old_poster = movie.get("poster")
    movie["title"] = title.strip()
    movie["year"] = int(year)
    copied = None
    if remove_poster:
        movie.pop("poster", None)
    elif poster_source:
        copied = copy_poster(poster_source)
        movie["poster"] = copied
    try:
        save_movies(movies)
    except OSError:
        _remove_unused_poster(copied, [])
        raise
    if remove_poster or copied:
        _remove_unused_poster(old_poster, movies)
    return movie

def delete_movie(movie_id):
    movies = load_movies()
    movie = find_movie(movies, movie_id)
    if movie is None:
        raise ValueError(f"Movie #{movie_id} was not found.")
    movies.remove(movie)
    save_movies(movies)
    _remove_unused_poster(movie.get("poster"), movies)
    return movie

def save_movie(fields, movie_id=None, poster_source=None, remove_poster=False):
    """Commit the whole editor draft in one atomic write."""
    title = fields.get("title", "").strip()
    if not title:
        raise ValueError("Please enter a movie title.")
    year = int(fields["year"])
    rating = int(fields.get("rating", 0))
    if not 1888 <= year <= 2100 or not 0 <= rating <= 10:
        raise ValueError("Check the release year and rating (1–10, or unrated).")
    movies = load_movies()
    existing = find_movie(movies, movie_id) if movie_id is not None else None
    if movie_id is not None and existing is None:
        raise ValueError("This movie no longer exists.")
    movie = dict(existing) if existing else {"id": max((int(m["id"]) for m in movies), default=0) + 1}
    old_poster = movie.get("poster")
    movie.update(fields)
    movie.update(title=title, year=year, rating=rating)
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