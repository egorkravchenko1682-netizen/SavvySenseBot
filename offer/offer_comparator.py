from __future__ import annotations

from typing import Any


class OfferComparator:
    """Сравнивает два предложения по подтверждённой стоимости."""

    def compare(
        self,
        first: dict[str, Any],
        second: dict[str, Any],
    ) -> dict[str, Any]:

        first_cost = first.get("real_cost")
        second_cost = second.get("real_cost")

        first_currency = first.get("real_cost_currency")
        second_currency = second.get("real_cost_currency")

        # 1. Сначала используем Real Cost
        if (
            first.get("real_cost_known") is True
            and second.get("real_cost_known") is True
            and first_currency
            and first_currency == second_currency
        ):
            return self._compare_values(
                first_cost,
                second_cost,
                first_currency,
                "real_cost",
            )

        # 2. Если Real Cost недоступен — используем цену товара
        first_price = first.get("price")
        second_price = second.get("price")

        first_currency = first.get("currency")
        second_currency = second.get("currency")

        if (
            first_price is not None
            and second_price is not None
            and first_currency
            and first_currency == second_currency
        ):
            return self._compare_values(
                first_price,
                second_price,
                first_currency,
                "price",
            )

        # 3. Сравнение невозможно
        return {
            "comparison": "unknown",
            "cheaper": None,
            "difference": None,
            "currency": None,
            "comparison_source": None,
        }

    @staticmethod
    def _compare_values(
        first_value: float,
        second_value: float,
        currency: str,
        source: str,
    ) -> dict[str, Any]:

        first_value = float(first_value)
        second_value = float(second_value)

        if first_value < second_value:
            comparison = "first_cheaper"
        elif second_value < first_value:
            comparison = "second_cheaper"
        else:
            comparison = "equal"

        return {
            "comparison": comparison,
            "cheaper": (
                "first"
                if comparison == "first_cheaper"
                else "second"
                if comparison == "second_cheaper"
                else None
            ),
            "difference": abs(first_value - second_value),
            "currency": currency,
            "comparison_source": source,
        }