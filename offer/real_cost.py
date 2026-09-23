from __future__ import annotations

from typing import Any


class RealCost:
    """Рассчитывает полную подтверждённую стоимость."""

    def calculate(
        self,
        offer: dict[str, Any],
    ) -> dict[str, Any]:

        price = offer.get("price")
        shipping = offer.get("shipping_cost")

        if price is None or shipping is None:
            return self._unknown()

        currency = offer.get("currency")
        shipping_currency = offer.get("shipping_currency")

        if currency != shipping_currency:
            return self._unknown()

        tax = offer.get("tax")
        duty = offer.get("duty")
        fee = offer.get("fee")

        if not offer.get("tax_known", False):
            return self._unknown()

        if not offer.get("duty_known", False):
            return self._unknown()

        if not offer.get("fee_known", False):
            return self._unknown()

        total = (
            float(price)
            + float(shipping)
            + float(tax or 0)
            + float(duty or 0)
            + float(fee or 0)
        )

        return {
            "real_cost": total,
            "real_cost_currency": currency,
            "real_cost_known": True,
        }

    @staticmethod
    def _unknown() -> dict[str, Any]:
        return {
            "real_cost": None,
            "real_cost_currency": None,
            "real_cost_known": False,
        }