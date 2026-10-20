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

def add_to_list():
    movies = load_movies()
    if movies is None:
        return
    title = input("Enter movie title: ").strip()
    while True:
        try:
            year = int(input("Enter movie year: ").strip())
            break
        except ValueError:
            print("Please enter a valid year.")
    movie_id = max((movie["id"] for movie in movies), default=0) + 1
    new_movie = {"id": movie_id, "title": title, "year": year}
    movies.append(new_movie)
    save_movies(movies)
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
    movie = next((movie for movie in movies if movie["id"] == movie_id), None)
    if movie is None:
        print(f"No movie found with ID {movie_id}.")
        return
    movies.remove(movie)
    save_movies(movies)
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
    movie = next((movie for movie in movies if movie["id"] == movie_id), None)
    if movie is None:
        print(f"No movie found with ID {movie_id}.")
        return
    new_title = input("Enter the new title: ").strip()
    while True:
        try:
            new_year = int(input("Enter the new year: ").strip())
            break
        except ValueError:
            print("Please enter a valid year.")
    movie["title"] = new_title
    movie["year"] = new_year
    save_movies(movies)
    print(f"Updated movie: {movie['title']} ({movie['year']})")

def search_in_list():
    movies = load_movies()
    if movies is None:
        return
    query = input("Enter a search query: ").strip()
    results = [movie for movie in movies if query.lower() in movie['title'].lower()]
    if not results:
        results = [movie for movie in movies if query.lower() in str(movie['year']) or query == str(movie['id'])]
    if results:
        for movie in results:
            print(f"{movie['id']}. {movie['title']} ({movie['year']})")
    else:
        print("No movies found matching your query.")
