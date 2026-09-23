from __future__ import annotations

from typing import Any


class SellerQualityScore:
    """Преобразует качество продавца в числовой показатель."""

    SCORES = {
        "high": 1.0,
        "medium": 0.7,
        "low": 0.3,
        "known": 0.5,
        "unknown": None,
    }

    def calculate(
        self,
        seller_quality: dict[str, Any],
    ) -> dict[str, Any]:

        quality = seller_quality.get(
            "seller_quality",
            "unknown",
        )

        score = self.SCORES.get(
            quality,
            None,
        )

        return {
            "seller_quality": quality,
            "seller_quality_score": score,
            "seller_quality_score_known": score is not None,
        }