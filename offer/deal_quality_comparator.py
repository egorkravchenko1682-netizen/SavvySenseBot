from __future__ import annotations

from typing import Any

from .quality_comparator import QualityComparator


class DealQualityComparator:
    """Находит лучшее предложение по стоимости и качеству."""

    def __init__(self) -> None:
        self.comparator = QualityComparator()

    def find_best(
        self,
        offers: list[dict[str, Any]],
    ) -> dict[str, Any]:

        if not offers:
            return {
                "best_offer": None,
                "comparison_known": False,
                "comparison_source": None,
            }

        best = None
        comparison_source = None

        for offer in offers:

            if best is None:
                best = offer
                continue

            result = self.comparator.compare(
                best,
                offer,
            )

            if result["better"] == "second":
                best = offer
                comparison_source = result["comparison_source"]

            elif result["better"] == "first":
                comparison_source = result["comparison_source"]

            elif result["better"] == "equal":
                if comparison_source is None:
                    comparison_source = (
                        result["comparison_source"]
                    )

        if best is None or comparison_source is None:
            return {
                "best_offer": None,
                "comparison_known": False,
                "comparison_source": None,
            }

        return {
            "best_offer": best,
            "comparison_known": True,
            "comparison_source": comparison_source,
        }