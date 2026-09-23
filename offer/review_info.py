from __future__ import annotations

from typing import Any


class ReviewInfo:
    """Нормализует информацию об отзывах товара."""

    def build(
        self,
        rating: float | None = None,
        review_count: int | None = None,
    ) -> dict[str, Any]:

        return {
            "product_rating": rating,
            "review_count": review_count,
            "reviews_known": (
                rating is not None
                or review_count is not None
            ),
        }