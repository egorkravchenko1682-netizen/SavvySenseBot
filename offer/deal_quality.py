from __future__ import annotations

from typing import Any


class DealQuality:
    """Формирует качество предложения с учётом полноты данных."""

    def calculate(
        self,
        seller: dict[str, Any],
        reviews: dict[str, Any],
        review_confidence: dict[str, Any] | None = None,
        offer_reliability: dict[str, Any] | None = None,
    ) -> dict[str, Any]:

        seller_score = seller.get(
            "seller_quality_score"
        )

        review_score = reviews.get(
            "review_quality_score"
        )

        confidence_score = None

        if review_confidence:
            confidence_score = review_confidence.get(
                "review_confidence_score"
            )

        reliability_score = None

        if offer_reliability:
            reliability_score = offer_reliability.get(
                "offer_reliability_score"
            )

        scores = [
            score
            for score in (
                seller_score,
                review_score,
                confidence_score,
                reliability_score,
            )
            if score is not None
        ]

        if not scores:
            return {
                "deal_quality_score": None,
                "deal_quality": None,
                "deal_quality_known": False,
            }

        score = sum(scores) / len(scores)

        known_count = len(scores)

        if known_count == 1:
            quality = "unknown"

        elif score >= 0.8:
            quality = "high"

        elif score >= 0.5:
            quality = "medium"

        else:
            quality = "low"

        return {
            "deal_quality_score": score,
            "deal_quality": quality,
            "deal_quality_known": known_count >= 2,
        }