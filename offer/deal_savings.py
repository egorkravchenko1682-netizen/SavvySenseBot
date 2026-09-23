from __future__ import annotations

from typing import Any


class DealSavings:
    """Рассчитывает экономию относительно бюджета."""

    def calculate(
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

        if value >= budget:
            return {
                "savings": 0.0,
                "savings_percent": 0.0,
                "savings_known": True,
                "currency": budget_currency.upper(),
            }

        savings = budget - value
        savings_percent = (savings / budget * 100) if budget > 0 else 0.0

        return {
            "savings": savings,
            "savings_percent": savings_percent,
            "savings_known": True,
            "currency": budget_currency.upper(),
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
            "savings": None,
            "savings_percent": None,
            "savings_known": False,
            "currency": None,
        }