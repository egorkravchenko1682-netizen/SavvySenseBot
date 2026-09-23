from __future__ import annotations

from typing import Any


class RealCost:
    """Рассчитывает подтверждённую стоимость предложения."""

    def calculate(
        self,
        offer: dict[str, Any],
    ) -> dict[str, Any]:

        price = offer.get("price")
        shipping = offer.get("shipping_cost")

        if price is None:
            return {
                "real_cost": None,
                "real_cost_known": False,
            }

        if shipping is None:
            return {
                "real_cost": None,
                "real_cost_known": False,
            }

        currency = offer.get("currency")
        shipping_currency = offer.get("shipping_currency")

        if currency != shipping_currency:
            return {
                "real_cost": None,
                "real_cost_known": False,
            }

        return {
            "real_cost": float(price) + float(shipping),
            "real_cost_known": True,
        }