from __future__ import annotations

from typing import Any

from .condition_candidates import ConditionCandidates


class DealCondition:
    """Подготавливает предложения с учётом состояния товара."""

    def __init__(self) -> None:
        self.candidates = ConditionCandidates()

    def apply(
        self,
        offers: list[dict[str, Any]],
        requested_condition: str = "any",
    ) -> dict[str, Any]:

        result = self.candidates.select(
            offers=offers,
            requested_condition=requested_condition,
        )

        return {
            "offers": result["matched"],
            "matched_count": result["matched_count"],
            "mismatched_count": result["mismatched_count"],
            "unknown_count": result["unknown_count"],
        }