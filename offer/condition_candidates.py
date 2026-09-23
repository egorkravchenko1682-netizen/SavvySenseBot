from __future__ import annotations

from typing import Any

from .condition_filter import ConditionFilter


class ConditionCandidates:
    """Фильтрует предложения по состоянию товара."""

    def __init__(self) -> None:
        self.filter = ConditionFilter()

    def select(
        self,
        offers: list[dict[str, Any]],
        requested_condition: str = "any",
    ) -> dict[str, Any]:

        matched = []
        mismatched = []
        unknown = []

        for offer in offers:

            result = self.filter.check(
                offer=offer,
                requested_condition=requested_condition,
            )

            if result["condition_match"] is True:
                matched.append(offer)

            elif result["condition_match"] is False:
                mismatched.append(offer)

            else:
                unknown.append(offer)

        return {
            "matched": matched,
            "mismatched": mismatched,
            "unknown": unknown,
            "matched_count": len(matched),
            "mismatched_count": len(mismatched),
            "unknown_count": len(unknown),
        }