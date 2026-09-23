from __future__ import annotations

import re
from typing import Any


class AvailabilityExtractor:
    """
    Определяет наличие товара.

    Возможные значения:

    in_stock
    out_of_stock
    preorder
    unavailable
    unknown
    """

    IN_STOCK_MARKERS = {
        "in stock",
        "in-stock",
        "available",
        "available now",
        "ready to ship",
        "ships now",
        "на складе",
        "в наличии",
        "есть в наличии",
        "доступен",
        "доступно",
    }

    OUT_OF_STOCK_MARKERS = {
        "out of stock",
        "out-of-stock",
        "sold out",
        "currently unavailable",
        "unavailable",
        "нет в наличии",
        "нет на складе",
        "распродано",
        "недоступен",
        "недоступно",
    }

    PREORDER_MARKERS = {
        "preorder",
        "pre-order",
        "pre order",
        "предзаказ",
        "предзаказ доступен",
    }

    def extract(
        self,
        data: dict[str, Any] | None = None,
        text: str | None = None,
    ) -> str:

        data = data or {}

        availability = self._extract_from_data(
            data
        )

        if availability:
            return availability

        if text:
            availability = self._extract_from_text(
                text
            )

            if availability:
                return availability

        return "unknown"

    def _extract_from_data(
        self,
        data: Any,
    ) -> str | None:

        if isinstance(data, dict):

            for key in (
                "availability",
                "availabilityStatus",
                "stock",
                "stockStatus",
                "inventoryStatus",
            ):

                if key not in data:
                    continue

                result = self._normalize(
                    data.get(key)
                )

                if result:
                    return result

            for value in data.values():

                result = self._extract_from_data(
                    value
                )

                if result:
                    return result

        elif isinstance(data, list):

            for item in data:

                result = self._extract_from_data(
                    item
                )

                if result:
                    return result

        return None

    def _extract_from_text(
        self,
        text: str,
    ) -> str | None:

        if not text:
            return None

        normalized = self._normalize_text(
            text
        )

        # Более специфичные статусы
        # проверяем раньше общего available.
        for marker in self.PREORDER_MARKERS:

            if self._contains_marker(
                normalized,
                self._normalize_text(marker),
            ):
                return "preorder"

        for marker in self.OUT_OF_STOCK_MARKERS:

            if self._contains_marker(
                normalized,
                self._normalize_text(marker),
            ):
                return "out_of_stock"

        for marker in self.IN_STOCK_MARKERS:

            if self._contains_marker(
                normalized,
                self._normalize_text(marker),
            ):
                return "in_stock"

        return None

    def _normalize(
        self,
        value: Any,
    ) -> str | None:

        if value is None:
            return None

        normalized = self._normalize_text(
            value
        )

        if not normalized:
            return None

        # Schema.org URLs.
        if "instock" in normalized:
            return "in_stock"

        if "outofstock" in normalized:
            return "out_of_stock"

        if "preorder" in normalized:
            return "preorder"

        if "soldout" in normalized:
            return "out_of_stock"

        if "unavailable" in normalized:
            return "unavailable"

        # Прямые значения.
        direct_values = {
            "in stock": "in_stock",
            "available": "in_stock",
            "out of stock": "out_of_stock",
            "sold out": "out_of_stock",
            "unavailable": "unavailable",
            "preorder": "preorder",
            "pre order": "preorder",
        }

        if normalized in direct_values:
            return direct_values[
                normalized
            ]

        # Проверяем текстовые маркеры.
        for marker in self.PREORDER_MARKERS:

            if self._contains_marker(
                normalized,
                self._normalize_text(marker),
            ):
                return "preorder"

        for marker in self.OUT_OF_STOCK_MARKERS:

            if self._contains_marker(
                normalized,
                self._normalize_text(marker),
            ):
                return "out_of_stock"

        for marker in self.IN_STOCK_MARKERS:

            if self._contains_marker(
                normalized,
                self._normalize_text(marker),
            ):
                return "in_stock"

        return None

    @staticmethod
    def _normalize_text(
        value: Any,
    ) -> str:

        if value is None:
            return ""

        text = str(
            value
        ).lower().strip()

        text = (
            text
            .replace("ё", "е")
            .replace("_", " ")
            .replace("-", " ")
            .replace("/", " ")
        )

        text = re.sub(
            r"\s+",
            " ",
            text,
        )

        return text

    @staticmethod
    def _contains_marker(
        text: str,
        marker: str,
    ) -> bool:

        if not marker:
            return False

        if marker in text:
            return True

        if len(marker) <= 4:

            return bool(
                re.search(
                    rf"\b{re.escape(marker)}\b",
                    text,
                )
            )

        return False