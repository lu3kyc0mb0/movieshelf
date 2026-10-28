from datetime import date

def build_insights(movies, collection_id="", today=None):
    today = today or date.today()
    selected = [movie for movie in movies if not collection_id or collection_id in movie.get("collections", [])]
    month_index = today.year * 12 + today.month - 1
    months = []
    month_counts = {}
    for offset in range(11, -1, -1):
        index = month_index - offset
        label = f"{index // 12:04d}-{index % 12 + 1:02d}"
        item = {"label": label, "count": 0, "rewatches": 0}
        months.append(item)
        month_counts[label] = item
    ratings = [{"rating": rating, "count": 0} for rating in range(1, 11)]
    total_views = 0
    rewatches = 0
    rated = 0
    rating_sum = 0
    undated = 0
    for movie in selected:
        dates = sorted(movie.get("watch_dates", []))
        total_views += len(dates)
        rewatches += max(0, len(dates) - 1)
        if movie.get("status") == "watched" and not dates:
            undated += 1
        for index, value in enumerate(dates):
            month = month_counts.get(value[:7])
            if month is not None:
                month["count"] += 1
                if index > 0:
                    month["rewatches"] += 1
        rating = movie.get("rating", 0)
        if type(rating) is int and 1 <= rating <= 10:
            ratings[rating - 1]["count"] += 1
            rated += 1
            rating_sum += rating
    return {"movies": len(selected), "totalViews": total_views, "rewatches": rewatches,
            "undatedWatched": undated, "rated": rated, "unrated": len(selected) - rated,
            "averageRating": f"{rating_sum / rated:.1f}" if rated else "—",
            "months": months, "maxMonth": max((item["count"] for item in months), default=0),
            "ratings": ratings, "maxRating": max((item["count"] for item in ratings), default=0)}
