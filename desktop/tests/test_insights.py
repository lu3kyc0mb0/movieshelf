import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from insights import build_insights

class InsightsTests(unittest.TestCase):
    def test_collection_trends_and_ratings(self):
        movies = [
            {"id": 1, "collections": ["a"], "status": "watched", "rating": 8,
             "watch_dates": ["2026-01-03", "2026-09-02", "2026-09-02"]},
            {"id": 2, "collections": ["a", "b"], "status": "watched", "rating": 8},
            {"id": 3, "collections": ["b"], "status": "watchlist", "rating": 0},
            {"id": 4, "collections": ["a"], "status": "watched", "rating": 4,
             "watch_dates": ["2024-02-01", "2025-10-01"]},
        ]
        report = build_insights(movies, "a", date(2026, 10, 29))
        self.assertEqual(report["movies"], 3)
        self.assertEqual(report["totalViews"], 5)
        self.assertEqual(report["rewatches"], 3)
        self.assertEqual(report["undatedWatched"], 1)
        self.assertEqual(report["averageRating"], "6.7")
        self.assertEqual(report["ratings"][7]["count"], 2)
        self.assertEqual(report["ratings"][3]["count"], 1)
        self.assertEqual(report["months"][0]["label"], "2025-11")
        self.assertEqual(report["months"][10]["label"], "2026-09")
        self.assertEqual(report["months"][10]["count"], 2)
        self.assertEqual(report["months"][10]["rewatches"], 2)
        self.assertEqual(build_insights(movies, "b", date(2026, 10, 29))["movies"], 2)

    def test_empty_collection(self):
        report = build_insights([], "", date(2026, 1, 1))
        self.assertEqual(report["months"][0]["label"], "2025-02")
        self.assertEqual(report["months"][-1]["label"], "2026-01")
        self.assertEqual(report["maxMonth"], 0)
        self.assertEqual(report["maxRating"], 0)
        self.assertEqual(report["averageRating"], "—")

if __name__ == "__main__":
    unittest.main()
