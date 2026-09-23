from __future__ import annotations

from typing import Any


class BudgetFilter:
    """Проверяет, укладывается ли предложение в заданный бюджет."""

    def check(
        self,
        offer: dict[str, Any],
        budget: float | None,
        budget_currency: str | None,
    ) -> dict[str, Any]:

        if budget is None or not budget_currency:
            return self._unknown()

        value, currency = self._get_value(offer)

        if value is None or not currency:
            return self._unknown()

        if currency.upper() != budget_currency.upper():
            return self._unknown()

        value = float(value)
        budget = float(budget)

        return {
            "within_budget": value <= budget,
            "budget_known": True,
            "budget_value": budget,
            "budget_currency": budget_currency.upper(),
            "offer_value": value,
            "offer_currency": currency.upper(),
        }

    @staticmethod
    def _get_value(
        offer: dict[str, Any],
    ) -> tuple[float | None, str | None]:

        if offer.get("real_cost_known") is True:
            return (
                offer.get("real_cost"),
                offer.get("real_cost_currency"),
            )

        if offer.get("price") is not None:
            return (
                offer.get("price"),
                offer.get("currency"),
            )

        return None, None

    @staticmethod
    def _unknown() -> dict[str, Any]:
        return {
            "within_budget": None,
            "budget_known": False,
            "budget_value": None,
            "budget_currency": None,
            "offer_value": None,
            "offer_currency": None,
        }