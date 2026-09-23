from __future__ import annotations

from typing import Any


class SellerQuality:
    """Определяет базовое качество продавца."""

    def evaluate(
        self,
        seller: dict[str, Any],
    ) -> dict[str, Any]:

        rating = seller.get("seller_rating")
        verified = seller.get("seller_verified")
        known = seller.get("seller_known", False)

        if rating is not None:
            rating = float(rating)

            if rating < 4.0:
                quality = "low"
            elif rating < 4.5:
                quality = "medium"
            else:
                quality = "high"

            return {
                "seller_quality": quality,
                "seller_quality_known": True,
                "seller_rating": rating,
            }

        if verified is True or known is True:
            return {
                "seller_quality": "known",
                "seller_quality_known": True,
                "seller_rating": None,
            }

        return {
            "seller_quality": "unknown",
            "seller_quality_known": False,
            "seller_rating": None,
        }