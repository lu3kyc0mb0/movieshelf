import json
import os
from pathlib import Path
import movie_store as store

DEFAULTS = {"theme": "dark", "animations": True, "show_statistics": True, "card_size": 190}

def load():
    try:
        values = json.loads((store.BASE_DIR / "settings.json").read_text(encoding="utf-8"))
        if not isinstance(values, dict):
            return dict(DEFAULTS)
    except (OSError, ValueError):
        return dict(DEFAULTS)
    return {"theme": values.get("theme") if values.get("theme") in ("light", "dark") else "dark",
            "animations": bool(values.get("animations", True)),
            "show_statistics": bool(values.get("show_statistics", True)),
            "card_size": max(155, min(245, int(values.get("card_size", 190)))) if str(values.get("card_size", 190)).isdigit() else 190}

def save(values):
    target = store.BASE_DIR / "settings.json"
    temporary = target.with_suffix(".tmp")
    temporary.write_text(json.dumps(values, indent=2), encoding="utf-8")
    os.replace(temporary, target)