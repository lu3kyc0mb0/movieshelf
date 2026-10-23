import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
STORE_PATH = ROOT / "desktop" / "movie_store.py"

def load_store(directory):
    specification = importlib.util.spec_from_file_location("test_movie_store_module", STORE_PATH)
    store = importlib.util.module_from_spec(specification)
    specification.loader.exec_module(store)
    store.BASE_DIR = directory
    store.MOVIES_FILE = directory / "movies.json"
    store.POSTERS_DIR = directory / "posters"
    store.COUNTER_FILE = directory / "movie_id_counter.json"
    store.LOCK_FILE = directory / "movies.json.lock"
    return store

class MovieStoreTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.directory = Path(self.temporary.name)
        self.store = load_store(self.directory)

    def tearDown(self):
        self.temporary.cleanup()

    def test_invalid_movie_fields_are_rejected_without_changing_file(self):
        invalid = [{"id": 1, "title": "Film", "year": 2000, "rating": "bad"}]
        self.store.MOVIES_FILE.write_text(json.dumps(invalid), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "rating"):
            self.store.load_movies()
        self.assertEqual(json.loads(self.store.MOVIES_FILE.read_text(encoding="utf-8")), invalid)

    def test_ids_are_not_reused_after_deletion(self):
        first = self.store.add_movie("First", 2000)
        second = self.store.add_movie("Second", 2001)
        self.store.delete_movie(second["id"])
        third = self.store.add_movie("Third", 2002)
        self.assertEqual([first["id"], second["id"], third["id"]], [1, 2, 3])

    def test_existing_highest_id_is_preserved_before_first_add(self):
        self.store.MOVIES_FILE.write_text(json.dumps([
            {"id": 4, "title": "First", "year": 2000},
            {"id": 9, "title": "Second", "year": 2001},
        ]), encoding="utf-8")
        self.store.delete_movie(9)
        self.assertEqual(self.store.add_movie("Third", 2002)["id"], 10)

    def test_failed_save_preserves_previous_collection(self):
        self.store.add_movie("First", 2000)
        original = self.store.MOVIES_FILE.read_bytes()
        with patch.object(self.store.os, "replace", side_effect=OSError("disk error")):
            with self.assertRaises(OSError):
                self.store.save_movies([])
        self.assertEqual(self.store.MOVIES_FILE.read_bytes(), original)
        self.assertEqual(list(self.directory.glob(".movies.json.*.tmp")), [])

    def test_failed_poster_copy_removes_partial_file(self):
        source = self.directory / "source.jpg"
        source.write_bytes(b"source")
        def fail_copy(_, destination):
            Path(destination).write_bytes(b"partial")
            raise OSError("copy failed")
        with patch.object(self.store.shutil, "copy2", side_effect=fail_copy):
            with self.assertRaises(OSError):
                self.store.copy_poster(source)
        self.assertEqual(list(self.store.POSTERS_DIR.iterdir()), [])

    def test_simultaneous_processes_keep_all_movies(self):
        code = (
            "import importlib.util, pathlib, sys; "
            "spec=importlib.util.spec_from_file_location('movie_store', sys.argv[1]); "
            "store=importlib.util.module_from_spec(spec); spec.loader.exec_module(store); "
            "base=pathlib.Path(sys.argv[2]); store.BASE_DIR=base; "
            "store.MOVIES_FILE=base/'movies.json'; store.POSTERS_DIR=base/'posters'; "
            "store.COUNTER_FILE=base/'movie_id_counter.json'; store.LOCK_FILE=base/'movies.json.lock'; "
            "[store.add_movie(str(i), 2000) for i in range(8)]"
        )
        processes = [subprocess.Popen([sys.executable, "-c", code, str(STORE_PATH), str(self.directory)],
                                      stdout=subprocess.PIPE, stderr=subprocess.PIPE) for _ in range(4)]
        for process in processes:
            output, error = process.communicate(timeout=30)
            self.assertEqual(process.returncode, 0, error.decode(errors="replace"))
        movies = self.store.load_movies()
        self.assertEqual(len(movies), 32)
        self.assertEqual(len({movie["id"] for movie in movies}), 32)

if __name__ == "__main__":
    unittest.main()
