from __future__ import annotations

from typing import Any

from .deal_candidates import DealCandidates
from .deal_comparator import DealComparator
from .deal_budget import DealBudget


class DealEngine:
    """Формирует базовую сделку с учётом бюджета."""

    def __init__(self) -> None:
        self.candidates = DealCandidates()
        self.comparator = DealComparator()
        self.budget = DealBudget()

    def evaluate(
        self,
        offers: list[dict[str, Any]],
        budget: float | None = None,
        budget_currency: str | None = None,
    ) -> dict[str, Any]:

        candidates = self.candidates.select(offers)

        exact = candidates["exact"]
        similar = candidates["similar"]

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

        exact_result = self.comparator.find_cheapest(
            exact_budget["within_budget"]
        )

        if exact_result["comparison_known"]:
            return self._result(
                deal_type="exact",
                result=exact_result,
                candidates=candidates,
                budget_result=exact_budget,
            )

        similar_result = self.comparator.find_cheapest(
            similar_budget["within_budget"]
        )

        if similar_result["comparison_known"]:
            return self._result(
                deal_type="similar",
                result=similar_result,
                candidates=candidates,
                budget_result=similar_budget,
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
        }

    @staticmethod
    def _result(
        deal_type: str,
        result: dict[str, Any],
        candidates: dict[str, Any],
        budget_result: dict[str, Any],
    ) -> dict[str, Any]:

        return {
            "deal_type": deal_type,
            "best_offer": result["cheapest"],
            "comparison_known": True,
            "comparison_source": result["comparison_source"],
            "exact_count": candidates["exact_count"],
            "similar_count": candidates["similar_count"],
            "within_budget_count": budget_result["within_budget_count"],
            "over_budget_count": budget_result["over_budget_count"],
        }