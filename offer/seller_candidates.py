from __future__ import annotations

from typing import Any


class SellerCandidates:
    """Разделяет предложения по наличию информации о продавце."""

    def select(
        self,
        offers: list[dict[str, Any]],
    ) -> dict[str, Any]:

        known = []
        unknown = []

        for offer in offers:

            if offer.get("seller_known") is True:
                known.append(offer)
            else:
                unknown.append(offer)

        return {
            "known": known,
            "unknown": unknown,
            "known_count": len(known),
            "unknown_count": len(unknown),
        }