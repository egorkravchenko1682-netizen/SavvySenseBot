from __future__ import annotations

from typing import Any


class ReviewConfidence:
    """Определяет доверие к рейтингу по количеству отзывов."""

    def calculate(
        self,
        review_count: int | None,
    ) -> dict[str, Any]:

        if review_count is None:
            return {
                "review_confidence": "unknown",
                "review_confidence_score": None,
                "review_confidence_known": False,
            }

        count = int(review_count)

        if count < 10:
            confidence = "low"
            score = 0.3

        elif count < 100:
            confidence = "medium"
            score = 0.6

        elif count < 1000:
            confidence = "high"
            score = 0.8

        else:
            confidence = "very_high"
            score = 1.0

        return {
            "review_confidence": confidence,
            "review_confidence_score": score,
            "review_confidence_known": True,
        }