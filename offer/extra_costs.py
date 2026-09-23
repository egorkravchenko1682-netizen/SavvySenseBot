from __future__ import annotations

from typing import Any


class ExtraCosts:
    """Хранит дополнительные расходы предложения."""

    def build(
        self,
        tax: float | None = None,
        duty: float | None = None,
        fee: float | None = None,
        currency: str | None = None,
    ) -> dict[str, Any]:

        known = all(
            value is not None
            for value in (tax, duty, fee)
        )

        return {
            "tax": tax,
            "duty": duty,
            "fee": fee,
            "currency": currency,
            "extra_costs_known": known,
        }