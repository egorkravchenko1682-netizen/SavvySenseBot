from __future__ import annotations

from typing import Any


class OfferRisk:
    """Оценивает риск использования предложения."""

    def calculate(
        self,
        offer: dict[str, Any],
    ) -> dict[str, Any]:

        risk_points = 0

        if offer.get("price") is None:
            risk_points += 1

        if not offer.get("currency"):
            risk_points += 1

        if offer.get("delivery_known") is not True:
            risk_points += 1

        if offer.get("page_valid") is not True:
            risk_points += 2

        if offer.get("condition_known") is not True:
            risk_points += 1

        if offer.get("seller_known") is not True:
            risk_points += 1

        if offer.get("reviews_known") is not True:
            risk_points += 1

        if risk_points >= 5:
            risk = "high"

        elif risk_points >= 3:
            risk = "medium"

        else:
            risk = "low"

        return {
            "offer_risk": risk,
            "offer_risk_points": risk_points,
            "offer_risk_known": True,
        }