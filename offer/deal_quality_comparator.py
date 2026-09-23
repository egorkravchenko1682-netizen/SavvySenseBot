from __future__ import annotations

from typing import Any

from .risk_aware_comparator import RiskAwareComparator


class DealQualityComparator:
    """Находит лучшее предложение по стоимости, качеству и риску."""

    def __init__(self) -> None:
        self.comparator = RiskAwareComparator()

    def find_best(
        self,
        offers: list[dict[str, Any]],
    ) -> dict[str, Any]:

        if not offers:
            return {
                "best_offer": None,
                "comparison_known": False,
                "comparison_source": None,
            }

        best = offers[0]

        comparison_source = (
            self._initial_source(best)
        )

        for offer in offers[1:]:

            result = self.comparator.compare(
                best,
                offer,
            )

            if result["better"] == "second":
                best = offer
                comparison_source = (
                    result["comparison_source"]
                )

            elif result["better"] == "first":
                comparison_source = (
                    result["comparison_source"]
                )

            elif result["better"] == "equal":
                if comparison_source is None:
                    comparison_source = (
                        result["comparison_source"]
                    )

        if comparison_source is None:
            return {
                "best_offer": None,
                "comparison_known": False,
                "comparison_source": None,
            }

        return {
            "best_offer": best,
            "comparison_known": True,
            "comparison_source": comparison_source,
        }

    @staticmethod
    def _initial_source(
        offer: dict[str, Any],
    ) -> str | None:

        if offer.get("real_cost_known") is True:
            return "real_cost"

        if offer.get("price") is not None:
            return "price"

        if offer.get("deal_quality_score") is not None:
            return "quality"

        if offer.get("risk_level_score") is not None:
            return "risk"

        return None