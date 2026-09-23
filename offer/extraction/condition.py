from __future__ import annotations

import re
from typing import Any


class ConditionExtractor:
    """
    Определяет состояние товара.

    Возможные значения:

    new
    used
    refurbished
    renewed
    open_box
    unknown

    Если состояние невозможно подтвердить,
    возвращается unknown.
    """

    CONDITIONS = {
        "new": {
            "new",
            "brand new",
            "new item",
            "новый",
            "новая",
            "новое",
        },
        "used": {
            "used",
            "pre owned",
            "pre-owned",
            "second hand",
            "б/у",
            "бу",
            "бывший в употреблении",
            "подержанный",
        },
        "refurbished": {
            "refurbished",
            "refurb",
            "factory refurbished",
            "manufacturer refurbished",
            "восстановленный",
            "восстановленный производителем",
        },
        "renewed": {
            "renewed",
            "amazon renewed",
            "renew",
        },
        "open_box": {
            "open box",
            "open-box",
            "открытая коробка",
            "товар с открытой упаковкой",
        },
    }

    def extract(
        self,
        data: dict[str, Any] | None = None,
        text: str | None = None,
    ) -> str:

        data = data or {}

        condition = self._extract_from_data(
            data
        )

        if condition:
            return condition

        if text:
            condition = self._extract_from_text(
                text
            )

            if condition:
                return condition

        return "unknown"

    def _extract_from_data(
        self,
        data: Any,
    ) -> str | None:

        if isinstance(data, dict):

            # Стандартные поля structured data.
            for key in (
                "itemCondition",
                "condition",
                "productCondition",
                "conditionType",
            ):

                if key not in data:
                    continue

                condition = self._normalize(
                    data.get(key)
                )

                if condition:
                    return condition

            # Рекурсивный поиск.
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

        # Более специфичные состояния
        # проверяем раньше общего "new".
        priority = (
            "refurbished",
            "renewed",
            "open_box",
            "used",
            "new",
        )

        for condition in priority:

            markers = self.CONDITIONS[
                condition
            ]

            for marker in markers:

                marker_normalized = (
                    self._normalize_text(
                        marker
                    )
                )

                if not marker_normalized:
                    continue

                if self._contains_marker(
                    normalized,
                    marker_normalized,
                ):
                    return condition

        return None

    def _normalize(
        self,
        value: Any,
    ) -> str | None:

        if value is None:
            return None

        text = self._normalize_text(
            value
        )

        if not text:
            return None

        # Schema.org URL.
        if "refurbishedcondition" in text:
            return "refurbished"

        if "usedcondition" in text:
            return "used"

        if "newcondition" in text:
            return "new"

        if "damagedcondition" in text:
            return "used"

        if "openbox" in text:
            return "open_box"

        # Прямые значения.
        for condition, markers in self.CONDITIONS.items():

            normalized_markers = {
                self._normalize_text(marker)
                for marker in markers
            }

            if text in normalized_markers:
                return condition

        # Если значение содержит маркер.
        for condition, markers in self.CONDITIONS.items():

            for marker in markers:

                marker_normalized = (
                    self._normalize_text(
                        marker
                    )
                )

                if (
                    marker_normalized
                    and marker_normalized in text
                ):
                    return condition

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

        if marker in text:
            return True

        # Для коротких маркеров используем
        # границы слова, чтобы не ловить
        # случайные совпадения.
        if len(marker) <= 4:

            return bool(
                re.search(
                    rf"\b{re.escape(marker)}\b",
                    text,
                )
            )

        return False