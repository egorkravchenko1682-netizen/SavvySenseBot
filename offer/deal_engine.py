from __future__ import annotations

from typing import Any

from .deal_candidates import DealCandidates
from .deal_comparator import DealComparator


class DealEngine:
    """Формирует базовую структуру лучшей сделки."""

    def __init__(self) -> None:
        self.candidates = DealCandidates()
        self.comparator = DealComparator()

    def evaluate(
        self,
        offers: list[dict[str, Any]],
    ) -> dict[str, Any]:

        candidates = self.candidates.select(offers)

        exact = candidates["exact"]
        similar = candidates["similar"]

        exact_result = self.comparator.find_cheapest(exact)

        if exact_result["comparison_known"]:
            return {
                "deal_type": "exact",
                "best_offer": exact_result["cheapest"],
                "comparison_known": True,
                "comparison_source": exact_result["comparison_source"],
                "exact_count": candidates["exact_count"],
                "similar_count": candidates["similar_count"],
            }

        similar_result = self.comparator.find_cheapest(similar)

        if similar_result["comparison_known"]:
            return {
                "deal_type": "similar",
                "best_offer": similar_result["cheapest"],
                "comparison_known": True,
                "comparison_source": similar_result["comparison_source"],
                "exact_count": candidates["exact_count"],
                "similar_count": candidates["similar_count"],
            }

        return {
            "deal_type": "unknown",
            "best_offer": None,
            "comparison_known": False,
            "comparison_source": None,
            "exact_count": candidates["exact_count"],
            "similar_count": candidates["similar_count"],
        }