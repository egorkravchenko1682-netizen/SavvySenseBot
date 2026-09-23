from __future__ import annotations

from typing import Any


class CurrencyEngine:
    """Конвертирует стоимость в целевую валюту."""

    def convert(
        self,
        amount: float | None,
        from_currency: str | None,
        to_currency: str,
        rates: dict[str, float],
    ) -> dict[str, Any]:

        if amount is None or not from_currency or not to_currency:
            return {
                "amount": None,
                "currency": to_currency,
                "conversion_known": False,
            }

        from_currency = from_currency.upper()
        to_currency = to_currency.upper()

        if from_currency == to_currency:
            return {
                "amount": float(amount),
                "currency": to_currency,
                "conversion_known": True,
            }

        if from_currency not in rates or to_currency not in rates:
            return {
                "amount": None,
                "currency": to_currency,
                "conversion_known": False,
            }

        base_amount = float(amount) / rates[from_currency]
        converted = base_amount * rates[to_currency]

        return {
            "amount": converted,
            "currency": to_currency,
            "conversion_known": True,
        }