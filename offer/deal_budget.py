from __future__ import annotations

from typing import Any

from .budget_filter import BudgetFilter


class DealBudget:
    """Фильтрует предложения по бюджету."""

    def __init__(self) -> None:
        self.filter = BudgetFilter()

    def apply(
        self,
        offers: list[dict[str, Any]],
        budget: float | None,
        budget_currency: str | None,
    ) -> dict[str, Any]:

        within_budget = []
        over_budget = []
        unknown = []

        for offer in offers:

            result = self.filter.check(
                offer=offer,
                budget=budget,
                budget_currency=budget_currency,
            )

            if result["within_budget"] is True:
                within_budget.append(offer)

            elif result["within_budget"] is False:
                over_budget.append(offer)

            else:
                unknown.append(offer)

        return {
            "within_budget": within_budget,
            "over_budget": over_budget,
            "unknown": unknown,
            "within_budget_count": len(within_budget),
            "over_budget_count": len(over_budget),
            "unknown_count": len(unknown),
        }