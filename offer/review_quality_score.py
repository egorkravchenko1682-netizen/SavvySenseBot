from __future__ import annotations

from typing import Any


class ReviewQualityScore:
    """Преобразует качество отзывов в числовой показатель."""

    SCORES = {
        "high": 1.0,
        "medium": 0.7,
        "low": 0.3,
        "unknown": None,
    }

    def calculate(
        self,
        review_quality: dict[str, Any],
    ) -> dict[str, Any]:

        quality = review_quality.get(
            "review_quality",
            "unknown",
        )

        score = self.SCORES.get(
            quality,
            None,
        )

        return {
            "review_quality": quality,
            "review_quality_score": score,
            "review_quality_score_known": score is not None,
        }