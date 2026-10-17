import json
from pathlib import Path


FILE_PATH = Path(__file__).with_name("movies.json")


def load_movies():
    try:
        with FILE_PATH.open("r", encoding="utf-8") as file:
            movies = json.load(file)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError as error:
        print(f"Cannot read movies.json: {error}")
        return None

    if not isinstance(movies, list):
        print("movies.json must contain a list of movies.")
        return None
    return movies


def save_movies(movies):
    with FILE_PATH.open("w", encoding="utf-8") as file:
        json.dump(movies, file, ensure_ascii=False, indent=2)
        file.write("\n")


def get_list():
    movies = load_movies()
    if movies is None:
        return
    if not movies:
        print("No movies yet.")
        return
    for movie in movies:
        print(f"{movie['id']}. {movie['title']} ({movie['year']})")
