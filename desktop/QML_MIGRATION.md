# The QML interface

MovieShelf keeps its Python application logic and uses Qt Quick/QML for the interface. This source update retains the v1.3.0 data format and application version. It does not rebuild published releases or modify the PySide2 legacy project.

## How the pieces connect

1. `main.py` starts Qt, registers the bundled Medeo Sans TTF files with `QFontDatabase`, loads `qml/Main.qml`, and exposes a `ShelfBackend` object to QML under the name `shelf`. A system font is used only if the bundled files cannot be loaded.
2. `qml_backend.py` reads the library through `movie_store.py`. Its `MovieModel` exposes each visible movie to the gallery. The backend applies navigation, search, filters and sorting before updating that model.
3. QML screens call backend methods when the user edits or saves something. Qt signals notify the screens when data changes, so titles, statistics, posters and translated labels update together.
4. `movie_store.py` remains responsible for validation, file locking, atomic writes, permanent IDs and poster copies. QML does not write JSON files directly.
5. `tmdb_service.py` sends asynchronous title, details and poster requests to TMDB. It passes a selected result to the same editor draft, which writes to the library only when Save succeeds.

## Screen files

| File | Purpose |
| --- | --- |
| `qml/Main.qml` | Sidebar, library, poster grid, search, notifications and application shortcuts. |
| `qml/MovieDetails.qml` | Readable movie overview, rating and review. |
| `qml/MovieEditor.qml` | Overview, review, organization and poster studio tabs; save and discard actions. |
| `qml/FilterPanel.qml` | Combined filters for years, ratings, status, favorites, genres, tags and collections. |
| `qml/SettingsSheet.qml` | Appearance, language, motion, statistics, poster size and backup export. |
| `qml/TmdbSheet.qml` | Personal TMDB key setup, title search and result selection. |
| `qml/InsightsSheet.qml` | Local viewing trends and rating distribution for the library or a custom collection. |
| `qml/CollectionsSheet.qml` | Create, rename and delete custom collections. |
| `qml/Poster.qml` | Image loading, rounded masking, crop positioning and image drops. |
| `qml/Theme.qml` | Shared colors, translation lookup and animation duration. |
| Other files in `qml/` | Shared buttons, icons, text fields, sliders, selectors and popup styling. |

## Editing and saving

Opening the editor creates a separate draft. Typing changes that draft, so Cancel can discard edits without touching `movies.json`. The backend compares the draft against its last saved snapshot to detect unsaved changes.

The Viewing history tab stores watch dates as an optional `watch_dates` list of ISO `YYYY-MM-DD` strings. Existing movies without this field open with an empty history. Repeated dates represent separate watches on the same day. Adding a date marks the movie watched; moving it back to Watchlist requires removing its viewing dates first. The history is saved with the movie and included in library backups.

`insights.py` calculates analytics from saved movies. Its 12 monthly buckets count recorded viewing dates, and its rating bins count films with personal scores from 1 to 10. Older watched films without dates are shown separately because their viewing month is unknown. Selecting a custom collection limits both charts and summary figures to movies in that collection. No TMDB request is involved.

Save validates the draft and writes it through `save_movie()`. Only after a successful write does the backend reset the unsaved state and refresh the library. If validation or writing fails, the editor stays open with the draft intact. Save & view also opens the saved movie's details.

Poster files are copied into the managed posters directory on save. Removing or replacing a poster uses the existing store's cleanup rules. A movie can belong to several custom collections. Removing a collection keeps its films; editing those films drops references to collections that no longer exist.

TMDB imports use a temporary poster file until Save. Discarding the draft removes that file. The imported TMDB ID is an optional field in `movies.json`; existing records remain valid. Credentials are saved per operating-system user under Qt's application configuration directory and are excluded from library backups. Requests use a personal v3 key or Read Access Token. The TMDB API's free use is limited to noncommercial projects under its terms.

## Rendering and cropping

The gallery uses a `GridView` with reusable delegates, so it creates visual cards around the visible area rather than constructing a widget for every film. Posters load asynchronously and use smooth texture filtering with mipmaps when reduced. The poster component applies a rounded mask through Qt Quick Effects.

Crop geometry follows the existing data: `mode` chooses fit or fill, `zoom` ranges from 1 to 3, and `x`/`y` range from -1 to 1. Dragging updates these values. The editor's three previews and the gallery use the same component and crop values. The original image is kept; cropping changes how it is displayed. Small source images still limit available detail.

Vector icons use Qt Quick Shapes. Buttons and navigation animate color, press scale or opacity. Turning off Smooth transitions reduces these animation durations to zero. Rendering quality still depends on the display scale, image quality and graphics driver; QML is not a guarantee that every graphics configuration will behave identically.

## Compatibility and verification

The current library, poster files, settings, IDs, translations, reviews and collection registry are reused without a data migration. The previous modern Widgets interface can still be started through `widgets_main.py`. `legacy-win32/` remains separate and unchanged.

The automated checks cover create/edit/delete flows, poster copying and cleanup, crop persistence, Unicode text, filtering, sorting, collections, backups, malformed files, failed writes, QML text input, dragging, settings, translations and unsaved close decisions. All writing tests use temporary directories. Rendering tests have been run on Windows with PySide6 6.12; macOS, Linux and packaged executables need their own validation before release.
