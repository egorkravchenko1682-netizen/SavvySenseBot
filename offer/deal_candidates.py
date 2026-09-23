from __future__ import annotations

from typing import Any


class DealCandidates:
    """Отбирает предложения, которые можно рассматривать для сделки."""

    def select(
        self,
        offers: list[dict[str, Any]],
    ) -> dict[str, Any]:

        exact = []
        similar = []

        for offer in offers:
            if offer.get("usable") is not True:
                continue

            status = offer.get("status")

            if status == "exact":
                exact.append(offer)

            elif status == "similar":
                similar.append(offer)

        return {
            "exact": exact,
            "similar": similar,
            "exact_count": len(exact),
            "similar_count": len(similar),
            "candidate_count": len(exact) + len(similar),
        }