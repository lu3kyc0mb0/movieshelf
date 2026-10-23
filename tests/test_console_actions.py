import importlib.util
import io
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
CONSOLE_PATH = ROOT / "console" / "actions.py"

class ConsoleActionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.directory = Path(self.temporary.name)
        specification = importlib.util.spec_from_file_location("test_console_actions_module", CONSOLE_PATH)
        self.actions = importlib.util.module_from_spec(specification)
        specification.loader.exec_module(self.actions)
        self.actions.FILE_PATH = self.directory / "movies.json"
        self.actions.COUNTER_FILE = self.directory / "movie_id_counter.json"
        self.actions.LOCK_FILE = self.directory / "movies.json.lock"

    def tearDown(self):
        self.temporary.cleanup()

    def test_search_includes_title_and_year_matches(self):
        self.actions.save_movies([
            {"id": 1, "title": "2001: A Space Odyssey", "year": 1968},
            {"id": 2, "title": "Another Film", "year": 2001},
        ])
        output = io.StringIO()
        with patch("builtins.input", return_value="2001"), redirect_stdout(output):
            self.actions.search_in_list()
        self.assertIn("2001: A Space Odyssey", output.getvalue())
        self.assertIn("Another Film", output.getvalue())

    def test_add_reprompts_for_empty_title_and_invalid_year(self):
        with patch("builtins.input", side_effect=["  ", "Film", "1200", "2020"]), redirect_stdout(io.StringIO()):
            self.actions.add_to_list()
        self.assertEqual(self.actions.load_movies(), [{"id": 1, "title": "Film", "year": 2020}])

    def test_deleted_id_is_not_reused(self):
        with patch("builtins.input", side_effect=["First", "2000", "Second", "2001", "2", "Third", "2002"]), redirect_stdout(io.StringIO()):
            self.actions.add_to_list()
            self.actions.add_to_list()
            self.actions.remove_from_list()
            self.actions.add_to_list()
        self.assertEqual([movie["id"] for movie in self.actions.load_movies()], [1, 3])

    def test_existing_highest_id_is_preserved_before_first_add(self):
        self.actions.save_movies([
            {"id": 4, "title": "First", "year": 2000},
            {"id": 9, "title": "Second", "year": 2001},
        ])
        with patch("builtins.input", side_effect=["9", "Third", "2002"]), redirect_stdout(io.StringIO()):
            self.actions.remove_from_list()
            self.actions.add_to_list()
        self.assertEqual([movie["id"] for movie in self.actions.load_movies()], [4, 10])

    def test_save_failure_is_reported_without_success_message(self):
        output = io.StringIO()
        with patch("builtins.input", side_effect=["Film", "2000"]), patch.object(self.actions, "save_movies", side_effect=OSError("disk full")), redirect_stdout(output):
            self.actions.add_to_list()
        self.assertIn("Cannot save movies.json", output.getvalue())
        self.assertNotIn("Added movie", output.getvalue())

    def test_simultaneous_console_sessions_keep_all_movies(self):
        code = (
            "import importlib.util, pathlib, sys; "
            "spec=importlib.util.spec_from_file_location('actions', sys.argv[1]); "
            "actions=importlib.util.module_from_spec(spec); spec.loader.exec_module(actions); "
            "base=pathlib.Path(sys.argv[2]); actions.FILE_PATH=base/'movies.json'; "
            "actions.COUNTER_FILE=base/'movie_id_counter.json'; actions.LOCK_FILE=base/'movies.json.lock'; "
            "actions.add_to_list()"
        )
        processes = [subprocess.Popen([sys.executable, "-c", code, str(CONSOLE_PATH), str(self.directory)],
                                      stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                      text=True) for _ in range(4)]
        for index, process in enumerate(processes):
            output, error = process.communicate(f"Film {index}\n2000\n", timeout=30)
            self.assertEqual(process.returncode, 0, error)
            self.assertIn("Added movie", output)
        movies = self.actions.load_movies()
        self.assertEqual(len(movies), 4)
        self.assertEqual(len({movie["id"] for movie in movies}), 4)

if __name__ == "__main__":
    unittest.main()
