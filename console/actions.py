import json
import os
import tempfile
from contextlib import contextmanager
from pathlib import Path

FILE_PATH = Path(__file__).with_name("movies.json")
COUNTER_FILE = Path(__file__).with_name("movie_id_counter.json")
LOCK_FILE = Path(__file__).with_name("movies.json.lock")

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

def _current_id_counter(movies):
    try:
        counter = json.loads(COUNTER_FILE.read_text(encoding="utf-8"))
    except FileNotFoundError:
        counter = {"last_id": 0}
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"Could not read movie ID counter: {error}") from error
    if not isinstance(counter, dict) or type(counter.get("last_id")) is not int or counter["last_id"] < 0:
        raise ValueError("Movie ID counter is invalid.")
    return max([counter["last_id"], *(movie["id"] for movie in movies)])

def _next_id(movies):
    movie_id = _current_id_counter(movies) + 1
    _atomic_write(COUNTER_FILE, json.dumps({"last_id": movie_id}) + "\n")
    return movie_id

def _ask_title(prompt):
    while True:
        title = input(prompt).strip()
        if title:
            return title
        print("Please enter a movie title.")

def _ask_year(prompt):
    while True:
        try:
            year = int(input(prompt).strip())
        except ValueError:
            print("Please enter a valid year.")
            continue
        if 1888 <= year <= 2100:
            return year
        print("Please enter a year between 1888 and 2100.")

def load_movies():
    try:
        with FILE_PATH.open("r", encoding="utf-8") as file:
            movies = json.load(file)
    except FileNotFoundError:
        return []
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        print(f"Cannot read movies.json: {error}")
        return None

    if not isinstance(movies, list):
        print("movies.json must contain a list of movies.")
        return None
    seen = set()
    for index, movie in enumerate(movies, 1):
        if (not isinstance(movie, dict) or type(movie.get("id")) is not int or movie["id"] < 1
                or movie["id"] in seen or not isinstance(movie.get("title"), str) or not movie["title"].strip()
                or type(movie.get("year")) is not int or not 1888 <= movie["year"] <= 2100):
            print(f"Movie #{index} has invalid data in movies.json.")
            return None
        seen.add(movie["id"])
    return movies

def save_movies(movies):
    _atomic_write(FILE_PATH, json.dumps(movies, ensure_ascii=False, indent=2) + "\n")

def _save_or_report(movies):
    try:
        save_movies(movies)
    except OSError as error:
        print(f"Cannot save movies.json: {error}")
        return False
    return True

def get_list():
    movies = load_movies()
    if movies is None:
        return
    if not movies:
        print("No movies yet.")
        return
    for movie in movies:
        print(f"{movie['id']}. {movie['title']} ({movie['year']})")

def add_to_list():
    movies = load_movies()
    if movies is None:
        return
    title = _ask_title("Enter movie title: ")
    year = _ask_year("Enter movie year: ")
    try:
        with _collection_lock():
            movies = load_movies()
            if movies is None:
                return
            movie_id = _next_id(movies)
            new_movie = {"id": movie_id, "title": title, "year": year}
            movies.append(new_movie)
            if not _save_or_report(movies):
                return
    except (OSError, ValueError) as error:
        print(f"Cannot add movie: {error}")
        return
    print(f"Added movie: {new_movie['title']} ({new_movie['year']})")

def remove_from_list():
    movies = load_movies()
    if movies is None:
        return
    while True:
        try:
            movie_id = int(input("Enter the ID of the movie to remove: "))
            break
        except ValueError:
            print("Please enter a valid ID.")
    try:
        with _collection_lock():
            movies = load_movies()
            if movies is None:
                return
            movie = next((movie for movie in movies if movie["id"] == movie_id), None)
            if movie is None:
                print(f"No movie found with ID {movie_id}.")
                return
            highest = _current_id_counter(movies)
            _atomic_write(COUNTER_FILE, json.dumps({"last_id": highest}) + "\n")
            movies.remove(movie)
            if not _save_or_report(movies):
                return
    except (OSError, ValueError) as error:
        print(f"Cannot remove movie: {error}")
        return
    print(f"Removed movie: {movie['title']} ({movie['year']})")

def edit_from_list():
    movies = load_movies()
    if movies is None:
        return
    while True:
        try:
            movie_id = int(input("Enter the ID of the movie to edit: "))
            break
        except ValueError:
            print("Please enter a valid ID.")
    if not any(movie["id"] == movie_id for movie in movies):
        print(f"No movie found with ID {movie_id}.")
        return
    new_title = _ask_title("Enter the new title: ")
    new_year = _ask_year("Enter the new year: ")
    try:
        with _collection_lock():
            movies = load_movies()
            if movies is None:
                return
            movie = next((movie for movie in movies if movie["id"] == movie_id), None)
            if movie is None:
                print(f"No movie found with ID {movie_id}.")
                return
            movie["title"] = new_title
            movie["year"] = new_year
            if not _save_or_report(movies):
                return
    except OSError as error:
        print(f"Cannot edit movie: {error}")
        return
    print(f"Updated movie: {movie['title']} ({movie['year']})")

def search_in_list():
    movies = load_movies()
    if movies is None:
        return
    query = input("Enter a search query: ").strip()
    results = [movie for movie in movies if query.casefold() in movie["title"].casefold()
               or query in str(movie["year"]) or query == str(movie["id"])]
    if results:
        for movie in results:
            print(f"{movie['id']}. {movie['title']} ({movie['year']})")
    else:
        print("No movies found matching your query.")
