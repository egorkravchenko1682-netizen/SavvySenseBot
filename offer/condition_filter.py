from __future__ import annotations

from typing import Any


class ConditionFilter:
    """Проверяет соответствие состояния товара запросу."""

    def check(
        self,
        offer: dict[str, Any],
        requested_condition: str = "any",
    ) -> dict[str, Any]:

        requested = str(
            requested_condition or "any"
        ).lower()

        actual = str(
            offer.get("condition") or "unknown"
        ).lower()

        if requested == "any":
            return {
                "condition_match": True,
                "condition_known": actual != "unknown",
            }

        if actual == "unknown":
            return {
                "condition_match": None,
                "condition_known": False,
            }

        return {
            "condition_match": actual == requested,
            "condition_known": True,
        }