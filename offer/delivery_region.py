from __future__ import annotations

from typing import Any


class DeliveryRegion:
    """Определяет доступность предложения для региона."""

    def check(
        self,
        delivery: dict[str, Any],
        country: str,
    ) -> dict[str, Any]:

        available = delivery.get("delivery_available")

        if available is True:
            return {
                "region": country,
                "available": True,
                "region_known": True,
            }

        if available is False:
            return {
                "region": country,
                "available": False,
                "region_known": True,
            }

        return {
            "region": country,
            "available": None,
            "region_known": False,
        }