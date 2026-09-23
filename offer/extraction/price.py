from __future__ import annotations

import re
from typing import Any


class PriceExtractor:
    """
    Извлекает цену и валюту из структурированных данных
    и текста страницы.

    Если цена не подтверждена —
    возвращает None, а не 0.
    """

    CURRENCY_SYMBOLS = {
        "$": "USD",
        "€": "EUR",
        "£": "GBP",
        "₽": "RUB",
        "₴": "UAH",
        "zł": "PLN",
        "¥": "CNY",
    }

    CURRENCY_CODES = {
        "usd": "USD",
        "eur": "EUR",
        "gbp": "GBP",
        "rub": "RUB",
        "byn": "BYN",
        "pln": "PLN",
        "cny": "CNY",
        "uah": "UAH",
    }

    PRICE_KEYS = (
        "price",
        "lowPrice",
        "highPrice",
        "salePrice",
        "currentPrice",
        "offerPrice",
        "amount",
    )

    CURRENCY_KEYS = (
        "priceCurrency",
        "currency",
        "currencyCode",
    )

    def extract(
        self,
        data: dict[str, Any] | None = None,
        text: str | None = None,
    ) -> dict[str, Any]:

        data = data or {}

        price = self._extract_from_data(data)
        currency = self._extract_currency(data)

        if price is None and text:
            price, text_currency = self._extract_from_text(text)

            if currency is None:
                currency = text_currency

        return {
            "price": price,
            "currency": currency,
            "price_known": price is not None,
        }

    def _extract_from_data(
        self,
        data: Any,
    ) -> float | None:

        if isinstance(data, dict):

            for key in self.PRICE_KEYS:

                if key not in data:
                    continue

                value = self._to_float(
                    data.get(key)
                )

                if value is not None:
                    return value

            for value in data.values():

                result = self._extract_from_data(
                    value
                )

                if result is not None:
                    return result

        elif isinstance(data, list):

            for item in data:

                result = self._extract_from_data(
                    item
                )

                if result is not None:
                    return result

        return None

    def _extract_currency(
        self,
        data: Any,
    ) -> str | None:

        if isinstance(data, dict):

            for key in self.CURRENCY_KEYS:

                value = data.get(key)

                currency = self._normalize_currency(
                    value
                )

                if currency:
                    return currency

            for value in data.values():

                result = self._extract_currency(
                    value
                )

                if result:
                    return result

        elif isinstance(data, list):

            for item in data:

                result = self._extract_currency(
                    item
                )

                if result:
                    return result

        return None

    def _extract_from_text(
        self,
        text: str,
    ) -> tuple[float | None, str | None]:

        if not text:
            return None, None

        patterns = [
            (
                r"([$€£₽₴])\s*"
                r"(\d[\d\s,]*(?:\.\d+)?)",
            ),
            (
                r"(\d[\d\s,]*(?:\.\d+)?)\s*"
                r"(USD|EUR|GBP|RUB|BYN|PLN|CNY|UAH)\b",
            ),
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                text,
                flags=re.IGNORECASE,
            )

            if not match:
                continue

            groups = match.groups()

            if len(groups) != 2:
                continue

            first = groups[0]
            second = groups[1]

            if first in self.CURRENCY_SYMBOLS:

                currency = self.CURRENCY_SYMBOLS[
                    first
                ]

                price = self._to_float(
                    second
                )

            else:

                price = self._to_float(
                    first
                )

                currency = self._normalize_currency(
                    second
                )

            if price is not None:
                return price, currency

        return None, None

    def _normalize_currency(
        self,
        value: Any,
    ) -> str | None:

        if value is None:
            return None

        normalized = str(
            value
        ).strip().lower()

        if normalized in self.CURRENCY_CODES:
            return self.CURRENCY_CODES[
                normalized
            ]

        if normalized in self.CURRENCY_SYMBOLS:
            return self.CURRENCY_SYMBOLS[
                normalized
            ]

        return None

    @staticmethod
    def _to_float(
        value: Any,
    ) -> float | None:

        if value is None:
            return None

        if isinstance(
            value,
            bool,
        ):
            return None

        try:

            if isinstance(
                value,
                (int, float),
            ):
                return float(value)

            text = str(
                value
            ).strip()

            text = re.sub(
                r"[^\d,.\-]",
                "",
                text,
            )

            if not text:
                return None

            # 1,299.99
            if (
                "," in text
                and "." in text
            ):
                if text.rfind(",") < text.rfind("."):
                    text = text.replace(
                        ",",
                        "",
                    )
                else:
                    text = text.replace(
                        ".",
                        "",
                    ).replace(
                        ",",
                        ".",
                    )

            # 1299,99
            elif "," in text:
                parts = text.split(",")

                if (
                    len(parts) == 2
                    and len(parts[1]) <= 2
                ):
                    text = (
                        parts[0]
                        + "."
                        + parts[1]
                    )
                else:
                    text = text.replace(
                        ",",
                        "",
                    )

            return float(text)

        except (
            TypeError,
            ValueError,
        ):
            return None