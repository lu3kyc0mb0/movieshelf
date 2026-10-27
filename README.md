# MovieShelf

A personal movie library, from a Python console project to a desktop collection and review journal.

![MovieShelf desktop](docs/desktop.png)

| Project | Description |
| --- | --- |
| [Desktop](desktop/README.md) | PySide6 interface, posters with adjustable framing, descriptions, reviews, ratings and collections. |
| [Console](console/README.md) | The original command-line project, preserved with its own data. |

## Launch the desktop app

```powershell
.\.venv\Scripts\python.exe -m pip install -r desktop/requirements.txt
.\.venv\Scripts\python.exe desktop/main.py
```

If `.venv` does not exist yet, create it with `python -m venv .venv`.

Your desktop collection uses `desktop/movies.json`, `desktop/posters/`, `desktop/movie_id_counter.json`, and `desktop/collections.json` if you create custom collections. Keep them together when moving the app. The desktop and console versions have separate collections.
