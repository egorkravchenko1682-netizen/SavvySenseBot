from __future__ import annotations

from typing import Any

from .quality_comparator import QualityComparator


class RiskAwareComparator:
    """Сравнивает предложения по цене, качеству и риску."""

    def __init__(self) -> None:
        self.comparator = QualityComparator()

    def compare(
        self,
        first: dict[str, Any],
        second: dict[str, Any],
    ) -> dict[str, Any]:

        result = self.comparator.compare(
            first,
            second,
        )

        if result["better"] in {
            "first",
            "second",
        }:
            return result

        if result["better"] == "equal":
            first_risk = first.get(
                "risk_level_score"
            )
            second_risk = second.get(
                "risk_level_score"
            )

            if (
                first_risk is not None
                and second_risk is not None
            ):
                if first_risk < second_risk:
                    return {
                        "better": "first",
                        "comparison_source": "risk",
                    }

                if second_risk < first_risk:
                    return {
                        "better": "second",
                        "comparison_source": "risk",
                    }

            return {
                "better": "equal",
                "comparison_source": result[
                    "comparison_source"
                ],
            }

        return {
            "better": None,
            "comparison_source": None,
        }