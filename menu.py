import json
from pathlib import Path
import actions

FILE_PATH = Path(__file__).with_name("menu.json")

def menu_data_init():
    try:
        with FILE_PATH.open("r", encoding="utf-8") as file:
            return json.load(file)
    except (OSError, json.JSONDecodeError) as error:
        print(f"Cannot read menu: {error}")
        return None

MENU_DATA = menu_data_init()

def menu_print():
    if MENU_DATA is None:
        return
    print(f"\n=== {MENU_DATA['label']} ===")
    for item in MENU_DATA["actions"]:
        print(f"{item['id']}. {item['name']}")


def select(number: str) -> bool:
    if MENU_DATA is None:
        return False

    item = next((item for item in MENU_DATA["actions"] if item["id"] == number), None)
    if item is None:
        print(f"Invalid choice: {number}")
        return True

    if item["action"] == "exit":
        print("Goodbye!")
        return False

    action = getattr(actions, item["action"], None)
    if action is None:
        print(f"Action {item['action']} is not implemented yet.")
    else:
        action()
    return True