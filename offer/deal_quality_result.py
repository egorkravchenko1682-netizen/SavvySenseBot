from __future__ import annotations

from typing import Any


class DealQualityResult:
    """Формирует единый результат качества сделки."""

    def build(
        self,
        deal: dict[str, Any],
    ) -> dict[str, Any]:

        best_offer = deal.get("best_offer")

        if best_offer is None:
            return {
                "deal_quality": None,
                "deal_quality_score": None,
                "deal_quality_known": False,
            }

        quality = best_offer.get("deal_quality")
        score = best_offer.get("deal_quality_score")

        return {
            "deal_quality": quality,
            "deal_quality_score": score,
            "deal_quality_known": (
                quality is not None
                and score is not None
            ),
        }