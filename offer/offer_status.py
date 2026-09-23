from __future__ import annotations

from typing import Any


class OfferStatus:
    """Определяет базовый статус предложения."""

    def get(
        self,
        offer: dict[str, Any],
    ) -> dict[str, Any]:

        if offer.get("page_valid") is False:
            return {
                "status": "rejected",
                "usable": False,
            }

        if offer.get("delivery_available") is False:
            return {
                "status": "unavailable",
                "usable": False,
            }

        if offer.get("match_type") == "unknown":
            return {
                "status": "unknown",
                "usable": False,
            }

        if offer.get("match_type") == "similar":
            return {
                "status": "similar",
                "usable": True,
            }

        if offer.get("match_type") == "exact":
            return {
                "status": "exact",
                "usable": True,
            }

        return {
            "status": "unknown",
            "usable": False,
        }