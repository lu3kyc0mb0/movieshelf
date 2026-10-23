import importlib.util
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONSOLE_DIR = ROOT / "console"
sys.path.insert(0, str(CONSOLE_DIR))

class ConsoleMenuTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.directory = Path(self.temporary.name)
        specification = importlib.util.spec_from_file_location("test_console_menu_module", CONSOLE_DIR / "menu.py")
        self.menu = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(self.menu)
        self.menu.FILE_PATH = self.directory / "menu.json"

    def tearDown(self):
        self.temporary.cleanup()

    def test_malformed_menu_is_rejected(self):
        self.menu.FILE_PATH.write_text(json.dumps({"label": "Menu", "actions": [5]}), encoding="utf-8")
        with redirect_stdout(io.StringIO()):
            self.assertIsNone(self.menu.menu_data_init())

    def test_unknown_action_is_rejected(self):
        self.menu.FILE_PATH.write_text(json.dumps({"label": "Menu", "actions": [
            {"id": "1", "name": "Invalid", "action": "_ask_title"}
        ]}), encoding="utf-8")
        with redirect_stdout(io.StringIO()):
            self.assertIsNone(self.menu.menu_data_init())

if __name__ == "__main__":
    unittest.main()
