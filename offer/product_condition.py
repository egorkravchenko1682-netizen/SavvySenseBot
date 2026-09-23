from __future__ import annotations

import re
from typing import Any


class ProductCondition:
    """Определяет состояние товара."""

    CONDITIONS = {
        "new": [
            "new",
            "brand new",
            "новый",
            "новое",
        ],
        "used": [
            "used",
            "pre-owned",
            "б/у",
            "бывший в употреблении",
        ],
        "refurbished": [
            "refurbished",
            "renewed",
            "восстановленный",
        ],
        "open_box": [
            "open box",
            "открытая коробка",
        ],
    }

    def detect(
        self,
        text: str | None,
    ) -> dict[str, Any]:

        if not text:
            return {
                "condition": "unknown",
                "condition_known": False,
            }

        normalized = re.sub(
            r"\s+",
            " ",
            text.lower(),
        )

        for condition, patterns in self.CONDITIONS.items():
            for pattern in patterns:
                if pattern in normalized:
                    return {
                        "condition": condition,
                        "condition_known": True,
                    }

        return {
            "condition": "unknown",
            "condition_known": False,
        }