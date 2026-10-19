# MovieShelf Desktop

A personal movie library and review journal built with PySide6.

## Run

From the repository root on Windows:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r desktop/requirements.txt
.\.venv\Scripts\python.exe desktop/main.py
```

## Your collection

- **Library:** all films, with IDs and ratings on the cards.
- **Watchlist:** films you want to watch.
- **Watched:** completed films.
- **Favorites:** personal favorites.
- **My reviews:** films with a rating or written review.
- Search titles, IDs, release years, descriptions and reviews.
- Sort by title, rating, year or most recently added ID.
- Change the poster card size with the library slider.

## Files and data

`main.py` contains the library window,
`editor.py` the movie editor,
`posters.py` the crop renderer,
`theme.py` the visual style,
`movie_store.py` persistence.

The existing `movies.json` and `posters/` are kept together in this folder. Keep both when moving or backing up your collection.

## Shortcuts

- `Ctrl+N`: add a film.
- `Ctrl+F`: open search.
- `Ctrl+S`: save the movie editor.
