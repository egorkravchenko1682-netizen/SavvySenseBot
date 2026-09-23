from __future__ import annotations

from typing import Any


class MatchResult:
    """Формирует единый результат сопоставления товара."""

    def build(
        self,
        match: dict[str, Any],
    ) -> dict[str, Any]:

        match_type = match.get("match_type", "unknown")

        return {
            "match_type": match_type,
            "exact_match": match_type == "exact",
            "similar_match": match_type == "similar",
            "match_known": match_type in {"exact", "similar"},
        }