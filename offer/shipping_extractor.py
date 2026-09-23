from __future__ import annotations

import re
from typing import Any


class ShippingExtractor:
    """
    Извлекает коммерческую стоимость доставки из структурированных
    данных и текста страницы.

    Важно:
    - неизвестная доставка -> None
    - бесплатная доставка -> 0.0 + shipping_free=True
    - не пытается вычислять доставку самостоятельно
    - не смешивает стоимость товара и стоимость доставки
    """

    CURRENCY_SYMBOLS = {
        "$": "USD",
        "€": "EUR",
        "£": "GBP",
        "₽": "RUB",
        "руб": "RUB",
        "р.": "RUB",
        "BYN": "BYN",
        "Br": "BYN",
        "¥": "CNY",
        "CNY": "CNY",
        "CN¥": "CNY",
        "₹": "INR",
        "₸": "KZT",
        "₴": "UAH",
        "₺": "TRY",
        "₩": "KRW",
        "AED": "AED",
        "PLN": "PLN",
    }

    SHIPPING_PATTERNS = [
        r"\bshipping\b",
        r"\bdelivery\b",
        r"\bpostage\b",
        r"\bfreight\b",
        r"\bshipping\s+fee\b",
        r"\bdelivery\s+fee\b",
        r"\bshipping\s+cost\b",
        r"\bdelivery\s+cost\b",
        r"\bshipping\s+charge\b",
        r"\bdelivery\s+charge\b",
        r"доставка",
        r"стоимость доставки",
        r"доставка товара",
        r"пересылка",
        r"доставк[аи]",
    ]

    FREE_PATTERNS = [
        r"\bfree\s+shipping\b",
        r"\bfree\s+delivery\b",
        r"\bshipping\s+is\s+free\b",
        r"\bdelivery\s+is\s+free\b",
        r"\bfree\s+postage\b",
        r"бесплатная доставка",
        r"доставка бесплатно",
        r"доставка\s*[-:]?\s*бесплатно",
    ]

    PRICE_PATTERN = re.compile(
        r"""
        (?P<currency>
            USD|EUR|GBP|RUB|BYN|CNY|CN¥|INR|KZT|UAH|TRY|KRW|AED|PLN
            |\$|€|£|₽|¥|₹|₸|₴|₺|₩
        )?
        \s*
        (?P<amount>
            \d{1,3}(?:[,\s]\d{3})*(?:[.,]\d{1,2})?
            |
            \d+(?:[.,]\d{1,2})?
        )
        \s*
        (?P<currency_after>
            USD|EUR|GBP|RUB|BYN|CNY|CN¥|INR|KZT|UAH|TRY|KRW|AED|PLN
            |\$|€|£|₽|¥|₹|₸|₴|₺|₩
        )?
        """,
        re.IGNORECASE | re.VERBOSE,
    )

    def extract(
        self,
        structured_data: Any = None,
        text: str | None = None,
    ) -> dict[str, Any]:
        """
        Основной entry point.

        Приоритет:
        1. structured data
        2. текст страницы
        """

        result = self._empty_result()

        # ---------------------------------------------------------
        # 1. Structured data
        # ---------------------------------------------------------

        structured_result = self._extract_from_structured_data(structured_data)

        if structured_result is not None:
            return structured_result

        # ---------------------------------------------------------
        # 2. Text
        # ---------------------------------------------------------

        if text:
            text_result = self._extract_from_text(text)

            if text_result is not None:
                return text_result

        return result

    # =============================================================
    # Structured data
    # =============================================================

    def _extract_from_structured_data(
        self,
        data: Any,
    ) -> dict[str, Any] | None:

        if not data:
            return None

        # Рекурсивно ищем shippingDetails / shippingRate
        found = self._walk_structured_data(data)

        if found is not None:
            return found

        return None

    def _walk_structured_data(
        self,
        value: Any,
    ) -> dict[str, Any] | None:

        if isinstance(value, dict):

            # -----------------------------------------------------
            # shippingDetails
            # -----------------------------------------------------

            if "shippingDetails" in value:
                result = self._parse_shipping_object(
                    value["shippingDetails"]
                )

                if result is not None:
                    return result

            # -----------------------------------------------------
            # shippingRate
            # -----------------------------------------------------

            if "shippingRate" in value:
                result = self._parse_shipping_object(
                    value["shippingRate"]
                )

                if result is not None:
                    return result

            # -----------------------------------------------------
            # Recursion
            # -----------------------------------------------------

            for child in value.values():
                result = self._walk_structured_data(child)

                if result is not None:
                    return result

        elif isinstance(value, list):

            for item in value:
                result = self._walk_structured_data(item)

                if result is not None:
                    return result

        return None

    def _parse_shipping_object(
        self,
        value: Any,
    ) -> dict[str, Any] | None:

        if value is None:
            return None

        if isinstance(value, list):

            for item in value:
                result = self._parse_shipping_object(item)

                if result is not None:
                    return result

            return None

        if not isinstance(value, dict):
            return None

        # ---------------------------------------------------------
        # Free shipping
        # ---------------------------------------------------------

        for key in (
            "freeShipping",
            "isFree",
        ):
            if value.get(key) is True:
                return {
                    "shipping_cost": 0.0,
                    "shipping_currency": self._normalize_currency(
                        value.get("currency")
                    ),
                    "shipping_known": True,
                    "shipping_free": True,
                    "shipping_source": "structured_data",
                }

        # ---------------------------------------------------------
        # Shipping rate
        # ---------------------------------------------------------

        rate = value.get("value")

        if rate is None:
            rate = value.get("price")

        if rate is not None:

            amount = self._parse_amount(rate)

            if amount is not None:

                currency = (
                    value.get("currency")
                    or value.get("priceCurrency")
                )

                return {
                    "shipping_cost": amount,
                    "shipping_currency": self._normalize_currency(currency),
                    "shipping_known": True,
                    "shipping_free": amount == 0,
                    "shipping_source": "structured_data",
                }

        return None

    # =============================================================
    # Text
    # =============================================================

    def _extract_from_text(
        self,
        text: str,
    ) -> dict[str, Any] | None:

        if not text:
            return None

        normalized = self._normalize_text(text)

        # ---------------------------------------------------------
        # Free shipping
        # ---------------------------------------------------------

        for pattern in self.FREE_PATTERNS:

            if re.search(pattern, normalized, re.IGNORECASE):

                return {
                    "shipping_cost": 0.0,
                    "shipping_currency": None,
                    "shipping_known": True,
                    "shipping_free": True,
                    "shipping_source": "text",
                }

        # ---------------------------------------------------------
        # Search around shipping keywords
        # ---------------------------------------------------------

        keyword_pattern = "|".join(
            f"(?:{pattern})"
            for pattern in self.SHIPPING_PATTERNS
        )

        match = re.search(
            rf"(?P<context>.{{0,80}}(?:{keyword_pattern}).{{0,100}})",
            normalized,
            re.IGNORECASE,
        )

        if not match:
            return None

        context = match.group("context")

        price = self._extract_price_from_context(context)

        if price is None:
            return None

        amount, currency = price

        return {
            "shipping_cost": amount,
            "shipping_currency": currency,
            "shipping_known": True,
            "shipping_free": amount == 0,
            "shipping_source": "text",
        }

    # =============================================================
    # Price parsing
    # =============================================================

    def _extract_price_from_context(
        self,
        text: str,
    ) -> tuple[float, str | None] | None:

        matches = list(self.PRICE_PATTERN.finditer(text))

        if not matches:
            return None

        # Берём ближайшую цену к shipping/delivery keyword.
        keyword_positions = []

        for pattern in self.SHIPPING_PATTERNS:

            for match in re.finditer(
                pattern,
                text,
                re.IGNORECASE,
            ):
                keyword_positions.append(match.start())

        if not keyword_positions:
            return None

        keyword_position = keyword_positions[0]

        best_match = min(
            matches,
            key=lambda m: abs(m.start() - keyword_position),
        )

        amount = self._parse_amount(
            best_match.group("amount")
        )

        if amount is None:
            return None

        currency = (
            best_match.group("currency")
            or best_match.group("currency_after")
        )

        return (
            amount,
            self._normalize_currency(currency),
        )

    # =============================================================
    # Helpers
    # =============================================================

    def _parse_amount(
        self,
        value: Any,
    ) -> float | None:

        if value is None:
            return None

        if isinstance(value, (int, float)):
            return float(value)

        value = str(value).strip()

        if not value:
            return None

        value = value.replace(" ", "")

        # 1,299.99
        if "," in value and "." in value:

            if value.rfind(".") > value.rfind(","):
                value = value.replace(",", "")

            else:
                value = value.replace(".", "")
                value = value.replace(",", ".")

        # 12,99
        elif "," in value:

            parts = value.split(",")

            if len(parts) == 2 and len(parts[1]) <= 2:
                value = value.replace(",", ".")

            else:
                value = value.replace(",", "")

        try:
            return float(value)

        except (TypeError, ValueError):
            return None

    def _normalize_currency(
        self,
        currency: Any,
    ) -> str | None:

        if currency is None:
            return None

        currency = str(currency).strip()

        if not currency:
            return None

        upper = currency.upper()

        if upper in self.CURRENCY_SYMBOLS:
            return self.CURRENCY_SYMBOLS[upper]

        if currency in self.CURRENCY_SYMBOLS:
            return self.CURRENCY_SYMBOLS[currency]

        if len(upper) == 3:
            return upper

        return None

    def _normalize_text(
        self,
        text: str,
    ) -> str:

        return re.sub(
            r"\s+",
            " ",
            text,
        ).strip()

    def _empty_result(self) -> dict[str, Any]:

        return {
            "shipping_cost": None,
            "shipping_currency": None,
            "shipping_known": False,
            "shipping_free": False,
            "shipping_source": None,
        }