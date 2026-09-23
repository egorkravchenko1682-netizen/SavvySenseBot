from __future__ import annotations

from typing import Any

from .offer_comparator import OfferComparator


class QualityComparator:
    """Сравнивает предложения по цене и качеству."""

    def __init__(self) -> None:
        self.price_comparator = OfferComparator()

    def compare(
        self,
        first: dict[str, Any],
        second: dict[str, Any],
    ) -> dict[str, Any]:

        price_result = self.price_comparator.compare(
            first,
            second,
        )

        comparison = price_result["comparison"]

        if comparison == "first_cheaper":
            return {
                "better": "first",
                "comparison_source": price_result["comparison_source"],
            }

        if comparison == "second_cheaper":
            return {
                "better": "second",
                "comparison_source": price_result["comparison_source"],
            }

        if comparison == "equal":
            first_quality = first.get("deal_quality_score")
            second_quality = second.get("deal_quality_score")

            if (
                first_quality is not None
                and second_quality is not None
            ):
                if first_quality > second_quality:
                    return {
                        "better": "first",
                        "comparison_source": "quality",
                    }

                if second_quality > first_quality:
                    return {
                        "better": "second",
                        "comparison_source": "quality",
                    }

            return {
                "better": "equal",
                "comparison_source": price_result["comparison_source"],
            }

        return {
            "better": None,
            "comparison_source": None,
        }