from __future__ import annotations

from typing import Any


class SellerInfo:
    """Нормализует информацию о продавце."""

    def build(
        self,
        seller: str | None = None,
        seller_rating: float | None = None,
        seller_reviews: int | None = None,
        seller_verified: bool | None = None,
    ) -> dict[str, Any]:

        return {
            "seller": seller,
            "seller_rating": seller_rating,
            "seller_reviews": seller_reviews,
            "seller_verified": seller_verified,
            "seller_known": seller is not None,
        }