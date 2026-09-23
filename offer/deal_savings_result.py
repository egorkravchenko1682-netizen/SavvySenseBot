from __future__ import annotations

from typing import Any

from .deal_savings import DealSavings


class DealSavingsResult:
    """Добавляет информацию об экономии к результату сделки."""

    def __init__(self) -> None:
        self.savings = DealSavings()

    def build(
        self,
        deal: dict[str, Any],
        budget: float | None,
        budget_currency: str | None,
    ) -> dict[str, Any]:

        result = dict(deal)

        best_offer = deal.get("best_offer")

        if best_offer is None:
            result.update(
                {
                    "savings": None,
                    "savings_percent": None,
                    "savings_known": False,
                    "savings_currency": None,
                }
            )
            return result

        savings = self.savings.calculate(
            offer=best_offer,
            budget=budget,
            budget_currency=budget_currency,
        )

        result.update(
            {
                "savings": savings["savings"],
                "savings_percent": savings["savings_percent"],
                "savings_known": savings["savings_known"],
                "savings_currency": savings["currency"],
            }
        )

        return result