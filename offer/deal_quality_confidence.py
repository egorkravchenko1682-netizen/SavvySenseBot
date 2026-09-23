from __future__ import annotations

from typing import Any


class DealQualityConfidence:
    """Определяет доверие к итоговой оценке качества сделки."""

    def calculate(
        self,
        offer: dict[str, Any],
    ) -> dict[str, Any]:

        checks = [
            offer.get("seller_quality_score") is not None,
            offer.get("review_quality_score") is not None,
            offer.get("review_confidence_score") is not None,
            offer.get("offer_reliability_score") is not None,
        ]

        known_count = sum(checks)

        if known_count == 0:
            return {
                "deal_quality_confidence": "unknown",
                "deal_quality_confidence_score": None,
                "deal_quality_confidence_known": False,
            }

        if known_count == 1:
            confidence = "low"
            score = 0.3

        elif known_count == 2:
            confidence = "medium"
            score = 0.6

        elif known_count == 3:
            confidence = "high"
            score = 0.8

        else:
            confidence = "very_high"
            score = 1.0

        return {
            "deal_quality_confidence": confidence,
            "deal_quality_confidence_score": score,
            "deal_quality_confidence_known": True,
        }