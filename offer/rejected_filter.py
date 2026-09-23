from __future__ import annotations

from typing import Any


class RejectedFilter:
    """Удаляет предложения, которые нельзя использовать."""

    def filter(self, offers: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            offer
            for offer in offers
            if offer.get("page_valid", True)
        ]