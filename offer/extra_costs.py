from __future__ import annotations

from typing import Any


class ExtraCosts:
    """Хранит дополнительные расходы и их подтверждение."""

    def build(
        self,
        tax: float | None = None,
        duty: float | None = None,
        fee: float | None = None,
        currency: str | None = None,
        tax_known: bool = False,
        duty_known: bool = False,
        fee_known: bool = False,
    ) -> dict[str, Any]:

        return {
            "tax": tax,
            "duty": duty,
            "fee": fee,
            "currency": currency,
            "tax_known": tax_known,
            "duty_known": duty_known,
            "fee_known": fee_known,
            "extra_costs_known": (
                tax_known
                and duty_known
                and fee_known
            ),
        }