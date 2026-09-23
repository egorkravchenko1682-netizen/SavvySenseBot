from __future__ import annotations

from typing import Any


class RiskLevel:
    """Нормализует уровень риска предложения."""

    LEVELS = {
        "low": 1,
        "medium": 2,
        "high": 3,
    }

    def evaluate(
        self,
        risk: dict[str, Any],
    ) -> dict[str, Any]:

        level = str(
            risk.get("offer_risk") or "unknown"
        ).lower()

        if level not in self.LEVELS:
            return {
                "risk_level": "unknown",
                "risk_level_score": None,
                "risk_level_known": False,
            }

        return {
            "risk_level": level,
            "risk_level_score": self.LEVELS[level],
            "risk_level_known": True,
        }