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
- Create and rename custom collections, then add any film to several collections.
- Add genres and tags in the editor's Organization tab. Separate names with commas.
- Search titles, IDs, release years, descriptions, reviews, genres and tags.
- Sort by title, rating, year or most recently added ID.
- Use Filters to combine year and rating ranges, watch status, favorites, genre, tag and custom collection.
- Change the poster card size with the library slider.
- Drop a local image onto the poster editor, adjust its crop, and preview it at three card sizes before saving.
- Change the interface language in Settings: English, Russian or Kazakh. The choice is saved for the next launch.

## Files and data

`main.py` contains the library window,
`editor.py` the movie editor,
`posters.py` the crop renderer,
`theme.py` the visual style,
`movie_store.py` persistence.

Your collection uses `movies.json`, `posters/`, `movie_id_counter.json`, and `collections.json` after you create a custom collection. Keep these files when moving your library. Settings → Export library backup includes the collection registry. `movies.json.lock` is created automatically to coordinate simultaneous app sessions.

## Shortcuts

- `Ctrl+N`: add a film.
- `Ctrl+F`: open search.
- `Ctrl+S`: save the movie editor.
