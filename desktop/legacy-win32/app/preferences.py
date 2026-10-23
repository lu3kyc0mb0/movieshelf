import json
import movie_store as store

DEFAULTS = {"theme": "dark", "animations": True, "show_statistics": True, "card_size": 190}

def load():
    path = store.BASE_DIR / "settings.json"
    try:
        values = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return dict(DEFAULTS)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"Could not read settings.json: {error}") from error
    if not isinstance(values, dict):
        raise ValueError("settings.json must contain an object.")
    result = dict(DEFAULTS)
    result.update(values)
    if result["theme"] not in ("light", "dark"):
        raise ValueError("settings.json has an invalid theme.")
    for key in ("animations", "show_statistics"):
        if type(result[key]) is not bool:
            raise ValueError(f"settings.json has an invalid {key} value.")
    if type(result["card_size"]) is not int or not 155 <= result["card_size"] <= 245:
        raise ValueError("settings.json has an invalid card size.")
    return result

def save(values):
    target = store.BASE_DIR / "settings.json"
    store._atomic_write(target, json.dumps(values, indent=2) + "\n")
