from __future__ import annotations

from typing import Any


class RiskDecision:
    """Определяет действие системы по уровню риска."""

    def decide(
        self,
        offer: dict[str, Any],
    ) -> dict[str, Any]:

        risk_level = offer.get("risk_level")

        if risk_level == "low":
            return {
                "risk_decision": "allow",
                "risk_decision_known": True,
            }

        if risk_level == "medium":
            return {
                "risk_decision": "allow_with_warning",
                "risk_decision_known": True,
            }

        if risk_level == "high":
            return {
                "risk_decision": "review",
                "risk_decision_known": True,
            }

        return {
            "risk_decision": "review",
            "risk_decision_known": False,
        }