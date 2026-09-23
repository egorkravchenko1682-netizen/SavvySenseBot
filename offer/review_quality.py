from __future__ import annotations

from typing import Any


class ReviewQuality:
    """Определяет базовое качество отзывов товара."""

    def evaluate(
        self,
        reviews: dict[str, Any],
    ) -> dict[str, Any]:

        rating = reviews.get("product_rating")
        count = reviews.get("review_count")

        if rating is None:
            return {
                "review_quality": "unknown",
                "review_quality_known": False,
            }

        rating = float(rating)

        if rating < 3.5:
            quality = "low"
        elif rating < 4.3:
            quality = "medium"
        else:
            quality = "high"

        return {
            "review_quality": quality,
            "review_quality_known": True,
            "product_rating": rating,
            "review_count": count,
        }