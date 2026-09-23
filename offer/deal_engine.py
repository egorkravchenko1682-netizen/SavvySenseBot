from __future__ import annotations

from typing import Any

from .deal_candidates import DealCandidates
from .deal_quality_comparator import DealQualityComparator
from .deal_budget import DealBudget
from .deal_condition import DealCondition


class DealEngine:
    """Формирует сделку с учётом состояния, бюджета и качества."""

    def __init__(self) -> None:
        self.candidates = DealCandidates()
        self.comparator = DealQualityComparator()
        self.budget = DealBudget()
        self.condition = DealCondition()

    def evaluate(
        self,
        offers: list[dict[str, Any]],
        budget: float | None = None,
        budget_currency: str | None = None,
        requested_condition: str = "any",
    ) -> dict[str, Any]:

        candidates = self.candidates.select(offers)

        condition_result = self.condition.apply(
            offers=candidates["exact"] + candidates["similar"],
            requested_condition=requested_condition,
        )

        filtered_offers = condition_result["offers"]

        exact = [
            offer
            for offer in filtered_offers
            if offer.get("status") == "exact"
        ]

        similar = [
            offer
            for offer in filtered_offers
            if offer.get("status") == "similar"
        ]

        exact_budget = self.budget.apply(
            exact,
            budget,
            budget_currency,
        )

        similar_budget = self.budget.apply(
            similar,
            budget,
            budget_currency,
        )

        exact_result = self.comparator.find_best(
            exact_budget["within_budget"]
        )

        if exact_result["comparison_known"]:
            return self._result(
                deal_type="exact",
                result=exact_result,
                candidates=candidates,
                condition_result=condition_result,
                exact_budget=exact_budget,
                similar_budget=similar_budget,
            )

        similar_result = self.comparator.find_best(
            similar_budget["within_budget"]
        )

        if similar_result["comparison_known"]:
            return self._result(
                deal_type="similar",
                result=similar_result,
                candidates=candidates,
                condition_result=condition_result,
                exact_budget=exact_budget,
                similar_budget=similar_budget,
            )

        return {
            "deal_type": "no_deal",
            "best_offer": None,
            "comparison_known": False,
            "comparison_source": None,
            "exact_count": candidates["exact_count"],
            "similar_count": candidates["similar_count"],
            "within_budget_count": (
                exact_budget["within_budget_count"]
                + similar_budget["within_budget_count"]
            ),
            "over_budget_count": (
                exact_budget["over_budget_count"]
                + similar_budget["over_budget_count"]
            ),
            "condition_matched_count": (
                condition_result["matched_count"]
            ),
            "condition_mismatched_count": (
                condition_result["mismatched_count"]
            ),
            "condition_unknown_count": (
                condition_result["unknown_count"]
            ),
        }

    @staticmethod
    def _result(
        deal_type: str,
        result: dict[str, Any],
        candidates: dict[str, Any],
        condition_result: dict[str, Any],
        exact_budget: dict[str, Any],
        similar_budget: dict[str, Any],
    ) -> dict[str, Any]:

        return {
            "deal_type": deal_type,
            "best_offer": result["best_offer"],
            "comparison_known": True,
            "comparison_source": result["comparison_source"],

            "exact_count": candidates["exact_count"],
            "similar_count": candidates["similar_count"],

            "within_budget_count": (
                exact_budget["within_budget_count"]
                + similar_budget["within_budget_count"]
            ),

            "over_budget_count": (
                exact_budget["over_budget_count"]
                + similar_budget["over_budget_count"]
            ),

            "condition_matched_count": (
                condition_result["matched_count"]
            ),

            "condition_mismatched_count": (
                condition_result["mismatched_count"]
            ),

            "condition_unknown_count": (
                condition_result["unknown_count"]
            ),
        }