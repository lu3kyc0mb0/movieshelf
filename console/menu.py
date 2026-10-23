import json
from pathlib import Path
import actions

FILE_PATH = Path(__file__).with_name("menu.json")
ACTIONS = {
    "get_list": actions.get_list,
    "add_to_list": actions.add_to_list,
    "remove_from_list": actions.remove_from_list,
    "edit_from_list": actions.edit_from_list,
    "search_in_list": actions.search_in_list,
}

def menu_data_init():
    try:
        with FILE_PATH.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        print(f"Cannot read menu: {error}")
        return None
    if (not isinstance(data, dict) or not isinstance(data.get("label"), str)
            or not isinstance(data.get("actions"), list)):
        print("menu.json has an invalid structure.")
        return None
    seen = set()
    for item in data["actions"]:
        if (not isinstance(item, dict) or not isinstance(item.get("id"), str)
                or not isinstance(item.get("name"), str) or not isinstance(item.get("action"), str)
                or item["id"] in seen or item["action"] not in (*ACTIONS, "exit")):
            print("menu.json contains an invalid action.")
            return None
        seen.add(item["id"])
    return data

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

    action = ACTIONS.get(item["action"])
    if action is None:
        print(f"Action {item['action']} is not implemented yet.")
    else:
        action()
    return True
