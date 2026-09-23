from __future__ import annotations

from typing import Any


class StrictProductMatcher:
    """Определяет точность совпадения предложения с искомым товаром."""

    def match(
        self,
        target: dict[str, Any],
        offer: dict[str, Any],
    ) -> dict[str, Any]:

        target_brand = str(target.get("brand") or "").lower()
        offer_brand = str(offer.get("brand") or "").lower()

        target_title = str(target.get("title") or "").lower()
        offer_title = str(offer.get("title") or "").lower()

        if not target_title or not offer_title:
            return {
                "match_type": "unknown",
                "exact_match": False,
            }

        if target_brand and offer_brand and target_brand != offer_brand:
            return {
                "match_type": "similar",
                "exact_match": False,
            }

        target_words = set(target_title.split())
        offer_words = set(offer_title.split())

        if target_words.issubset(offer_words):
            return {
                "match_type": "exact",
                "exact_match": True,
            }

        return {
            "match_type": "similar",
            "exact_match": False,
        }