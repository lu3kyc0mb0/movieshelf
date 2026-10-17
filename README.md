# MovieShelf

A small command-line movie collection built with Python. MovieShelf is a place to keep track of the films you love and a hands-on project for learning how to organize a Python application, work with JSON, and build an interactive menu.

## Project structure

```text
MovieShelf/
├── main.py       # Runs the input loop
├── menu.py       # Loads the menu and dispatches choices
├── menu.json     # Menu labels and action names
├── actions.py    # Reads, saves, and displays movies
└── movies.json   # The movie collection
```

## Movie data

Each movie can use this format:

```json
{
  "id": 1,
  "title": "Interstellar",
  "year": 2014
}
```