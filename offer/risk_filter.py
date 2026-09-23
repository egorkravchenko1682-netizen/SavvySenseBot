from __future__ import annotations

from typing import Any


class RiskFilter:
    """Разделяет предложения по уровню риска."""

    def select(
        self,
        offers: list[dict[str, Any]],
    ) -> dict[str, Any]:

        safe = []
        risky = []
        unknown = []

        for offer in offers:

            level = offer.get("risk_level")

            if level in {"low", "medium"}:
                safe.append(offer)

            elif level == "high":
                risky.append(offer)

            else:
                unknown.append(offer)

        return {
            "safe": safe,
            "risky": risky,
            "unknown": unknown,
            "safe_count": len(safe),
            "risky_count": len(risky),
            "unknown_count": len(unknown),
        }