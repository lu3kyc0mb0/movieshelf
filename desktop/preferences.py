import copy
import json
import re
import keyboard
import movie_store as store

PALETTES = {
    "dark": dict(background="#17181c", sidebar="#1f2026", surface="#25262e", elevated="#30313b", hover="#353743", line="#353640", text="#f3f3f7", secondary="#a3a5b5", accent="#409cff", selected="#253b56", danger="#ff858c", gold="#f2cd7d", onAccent="#ffffff"),
    "light": dict(background="#fafafc", sidebar="#f1f2f5", surface="#ffffff", elevated="#eff0f4", hover="#e7e9ef", line="#e4e6ed", text="#242531", secondary="#747785", accent="#007aff", selected="#e1edfc", danger="#cf3548", gold="#a77821", onAccent="#ffffff"),
}
DEFAULTS = {"theme": "dark", "theme_style": "dark", "animations": True, "show_statistics": True, "card_size": 190, "language": "en",
            "font_family": "Medeo Sans", "text_scale": 1.0, "ui_scale": 1.0, "colors": {}, "theme_name": "", "shortcuts": keyboard.DEFAULTS,
            "custom_themes": [], "custom_theme_index": -1}

def validate(values):
    if not isinstance(values, dict):
        raise ValueError("Settings must contain an object.")
    result = copy.deepcopy(DEFAULTS)
    result.update({key: value for key, value in values.items() if key in DEFAULTS})
    if "theme_style" not in values:
        result["theme_style"] = result["theme"]
    if not isinstance(result["theme"], str) or result["theme"] not in PALETTES or result["language"] not in ("en", "ru", "kk"):
        raise ValueError("Invalid appearance or language.")
    if result["theme_style"] not in ("light", "dark", "contrast", "custom"):
        raise ValueError("Invalid theme style.")
    for key in ("animations", "show_statistics"):
        if type(result[key]) is not bool:
            raise ValueError("Invalid accessibility settings.")
    if type(result["card_size"]) is not int or not 155 <= result["card_size"] <= 245:
        raise ValueError("Invalid poster size.")
    for key, low, high in (("text_scale", 0.85, 1.5), ("ui_scale", 0.75, 2.0)):
        if type(result[key]) not in (int, float) or not low <= result[key] <= high:
            raise ValueError("Invalid interface scale.")
    for key in ("font_family", "theme_name"):
        if not isinstance(result[key], str) or len(result[key]) > 150:
            raise ValueError("Invalid font or theme name.")
    colors = result["colors"]
    if not isinstance(colors, dict) or set(colors) - set(PALETTES["dark"]):
        raise ValueError("Invalid theme colors.")
    if any(not isinstance(value, str) or not re.fullmatch(r"#[0-9a-fA-F]{6}", value) for value in colors.values()):
        raise ValueError("Use colors in #RRGGBB format.")
    result["shortcuts"] = keyboard.validate(result["shortcuts"])
    themes = result["custom_themes"]
    if not isinstance(themes, list) or len(themes) > 100:
        raise ValueError("Invalid custom themes.")
    fields = ("theme", "theme_name", "colors", "font_family", "text_scale")
    normalized = []
    for theme in themes:
        if not isinstance(theme, dict):
            raise ValueError("Invalid custom theme.")
        checked = validate({key: theme[key] for key in fields if key in theme})
        normalized.append({key: checked[key] for key in fields})
    result["custom_themes"] = normalized
    if type(result["custom_theme_index"]) is not int or not -1 <= result["custom_theme_index"] < max(1, len(normalized)):
        raise ValueError("Invalid custom theme selection.")
    if not normalized and result["theme_style"] == "custom" and result["theme_name"]:
        result["custom_themes"] = [{key: result[key] for key in fields}]
        result["custom_theme_index"] = 0
    return result

def load():
    path = store.BASE_DIR / "settings.json"
    try:
        return validate(json.loads(path.read_text(encoding="utf-8")))
    except FileNotFoundError:
        return copy.deepcopy(DEFAULTS)
    except (OSError, UnicodeError, ValueError) as error:
        raise ValueError(f"Could not read settings.json: {error}") from error

def save(values):
    store._atomic_write(store.BASE_DIR / "settings.json", json.dumps(validate(values), ensure_ascii=False, indent=2) + "\n")

def theme_document(values):
    settings = validate({key: values[key] for key in ("theme", "theme_style", "theme_name", "colors", "font_family", "text_scale") if key in values})
    colors = dict(PALETTES[settings["theme"]])
    colors.update(settings["colors"])
    return {"format": "movieshelf-theme", "version": 1, "name": settings["theme_name"], "mode": settings["theme"], "colors": colors,
            "font_family": settings["font_family"], "text_scale": settings["text_scale"]}

def read_theme(path):
    if path.stat().st_size > 65536:
        raise ValueError("Theme file is too large.")
    document = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(document, dict) or document.get("format") != "movieshelf-theme" or type(document.get("version")) is not int or document["version"] != 1:
        raise ValueError("Unsupported theme file.")
    values = {"theme": document.get("mode"), "theme_style": "custom", "theme_name": document.get("name", ""), "colors": document.get("colors")}
    for key in ("font_family", "text_scale"):
        if key in document:
            values[key] = document[key]
    settings = validate(values)
    return {key: settings[key] for key in values}
