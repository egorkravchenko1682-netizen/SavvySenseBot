from __future__ import annotations

from typing import Any


class DealResult:
    """Формирует единый результат сделки."""

    def build(
        self,
        deal: dict[str, Any],
    ) -> dict[str, Any]:

        best_offer = deal.get("best_offer")

        return {
            "deal_type": deal.get("deal_type", "unknown"),
            "best_offer": best_offer,

            "comparison_known": deal.get(
                "comparison_known",
                False,
            ),

            "comparison_source": deal.get(
                "comparison_source"
            ),

            "exact_count": deal.get(
                "exact_count",
                0,
            ),

            "similar_count": deal.get(
                "similar_count",
                0,
            ),

            "within_budget_count": deal.get(
                "within_budget_count",
                0,
            ),

            "over_budget_count": deal.get(
                "over_budget_count",
                0,
            ),

            "deal_known": (
                deal.get("deal_type") in {
                    "exact",
                    "similar",
                }
                and best_offer is not None
            ),
        }