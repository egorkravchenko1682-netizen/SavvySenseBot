from __future__ import annotations

from typing import Any


class OfferReliability:
    """Оценивает надёжность данных предложения."""

    def calculate(
        self,
        offer: dict[str, Any],
    ) -> dict[str, Any]:

        checks = []

        if offer.get("price") is not None:
            checks.append(True)
        else:
            checks.append(False)

        if offer.get("currency"):
            checks.append(True)
        else:
            checks.append(False)

        if offer.get("delivery_known") is True:
            checks.append(True)
        else:
            checks.append(False)

        if offer.get("page_valid") is True:
            checks.append(True)
        else:
            checks.append(False)

        if offer.get("condition_known") is True:
            checks.append(True)
        else:
            checks.append(False)

        score = sum(checks) / len(checks)

        if score >= 0.8:
            reliability = "high"
        elif score >= 0.5:
            reliability = "medium"
        else:
            reliability = "low"

        return {
            "offer_reliability": reliability,
            "offer_reliability_score": score,
            "offer_reliability_known": True,
        }