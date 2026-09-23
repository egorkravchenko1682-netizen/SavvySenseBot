from __future__ import annotations

from typing import Any


class DealQuality:
    """Формирует базовое качество предложения."""

    def calculate(
        self,
        seller: dict[str, Any],
        reviews: dict[str, Any],
    ) -> dict[str, Any]:

        seller_score = seller.get(
            "seller_quality_score"
        )

        review_score = reviews.get(
            "review_quality_score"
        )

        scores = [
            score
            for score in (
                seller_score,
                review_score,
            )
            if score is not None
        ]

        if not scores:
            return {
                "deal_quality_score": None,
                "deal_quality_known": False,
            }

        score = sum(scores) / len(scores)

        if score >= 0.8:
            quality = "high"
        elif score >= 0.5:
            quality = "medium"
        else:
            quality = "low"

        return {
            "deal_quality_score": score,
            "deal_quality": quality,
            "deal_quality_known": True,
        }