from __future__ import annotations

from typing import Any

from .offer_comparator import OfferComparator


class DealComparator:
    """Находит самое дешёвое сравнимое предложение."""

    def __init__(self) -> None:
        self.comparator = OfferComparator()

    def find_cheapest(
        self,
        offers: list[dict[str, Any]],
    ) -> dict[str, Any]:

        if not offers:
            return {
                "cheapest": None,
                "comparison_known": False,
                "comparison_source": None,
            }

        cheapest = None
        comparison_source = None

        for offer in offers:

            if cheapest is None:
                cheapest = offer
                comparison_source = self._source(offer)
                continue

            result = self.comparator.compare(
                cheapest,
                offer,
            )

            if result["comparison"] == "second_cheaper":
                cheapest = offer
                comparison_source = result["comparison_source"]

            elif result["comparison"] == "first_cheaper":
                comparison_source = result["comparison_source"]

        if cheapest is None:
            return {
                "cheapest": None,
                "comparison_known": False,
                "comparison_source": None,
            }

        if comparison_source is None:
            return {
                "cheapest": None,
                "comparison_known": False,
                "comparison_source": None,
            }

        return {
            "cheapest": cheapest,
            "comparison_known": True,
            "comparison_source": comparison_source,
        }

    @staticmethod
    def _source(
        offer: dict[str, Any],
    ) -> str | None:

        if offer.get("real_cost_known") is True:
            return "real_cost"

        if offer.get("price") is not None:
            return "price"

        return None