from __future__ import annotations

import re
from typing import Any


class PriceExtractor:
    """
    Commercial Price Extractor для SAVVY SENSE.

    Приоритет источников:

        1. Structured data / JSON-LD
        2. Коммерческие вложенные структуры
        3. Meta / itemprop / data-* поля
        4. Текст страницы

    Важный принцип:

        UNKNOWN != 0

    Если цена не подтверждена,
    возвращается None.

    Extractor старается отличать:
        - текущую цену
        - sale price
        - regular/list price
        - диапазон цен
        - валюту
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

    # Наиболее вероятные поля текущей цены.
    CURRENT_PRICE_KEYS = (
        "price",
        "currentPrice",
        "salePrice",
        "sellingPrice",
        "offerPrice",
        "finalPrice",
        "discountPrice",
        "current_price",
        "sale_price",
        "selling_price",
        "offer_price",
        "final_price",
        "discount_price",
    )

    # Цена до скидки.
    REGULAR_PRICE_KEYS = (
        "regularPrice",
        "originalPrice",
        "listPrice",
        "basePrice",
        "wasPrice",
        "oldPrice",
        "retailPrice",
        "msrp",
        "regular_price",
        "original_price",
        "list_price",
        "base_price",
        "was_price",
        "old_price",
        "retail_price",
    )

    # Поля, которые часто содержат стоимость,
    # но сами по себе имеют более низкий приоритет.
    GENERIC_PRICE_KEYS = (
        "amount",
        "value",
        "unitPrice",
        "unit_price",
    )

    CURRENCY_KEYS = (
        "priceCurrency",
        "currency",
        "currencyCode",
        "currency_code",
        "price_currency",
    )

    PRICE_META_KEYS = (
        "product:price:amount",
        "product:price",
        "og:price:amount",
        "price",
        "price.amount",
        "product-price",
        "product_price",
        "current-price",
        "current_price",
        "sale-price",
        "sale_price",
    )

    PRICE_ATTRIBUTE_KEYS = (
        "price",
        "data-price",
        "data-product-price",
        "data-product_price",
        "data-sale-price",
        "data-sale_price",
        "data-current-price",
        "data-current_price",
        "data-price-amount",
        "data-price_amount",
    )

    # Ключи, которые сами по себе не должны
    # считаться ценой товара.
    EXCLUDED_PRICE_KEYS = {
        "shipping",
        "shippingprice",
        "shipping_price",
        "delivery",
        "deliveryprice",
        "delivery_price",
        "tax",
        "taxes",
        "taxprice",
        "tax_price",
        "duty",
        "duties",
        "fee",
        "fees",
        "discount",
        "discountamount",
        "discount_amount",
    }

    def extract(
        self,
        data: dict[str, Any] | None = None,
        text: str | None = None,
    ) -> dict[str, Any]:

        data = data or {}

        result = self._empty_result()

        # ---------------------------------------------------------
        # 1. Structured / embedded data
        # ---------------------------------------------------------

        structured = self._extract_structured_price(
            data
        )

        if structured["price"] is not None:

            result.update(
                structured
            )

            return result

        # ---------------------------------------------------------
        # 2. Meta / itemprop / data-* style dictionaries
        # ---------------------------------------------------------

        commercial = self._extract_commercial_fields(
            data
        )

        if commercial["price"] is not None:

            result.update(
                commercial
            )

            return result

        # ---------------------------------------------------------
        # 3. Generic recursive data search
        # ---------------------------------------------------------

        generic = self._extract_from_data(
            data
        )

        if generic["price"] is not None:

            result.update(
                generic
            )

            return result

        # ---------------------------------------------------------
        # 4. Page text
        # ---------------------------------------------------------

        if text:

            text_result = self._extract_from_text(
                text
            )

            if text_result["price"] is not None:

                result.update(
                    text_result
                )

                return result

        return result

    def _empty_result(self) -> dict[str, Any]:

        return {
            "price": None,
            "currency": None,
            "price_known": False,
            "price_source": None,
            "regular_price": None,
            "regular_price_known": False,
        }

    # =========================================================
    # STRUCTURED DATA
    # =========================================================

    def _extract_structured_price(
        self,
        data: Any,
    ) -> dict[str, Any]:

        result = self._empty_result()

        if isinstance(data, dict):

            # Сначала ищем наиболее надёжные
            # текущие коммерческие поля.
            current = self._find_price_by_keys(
                data,
                self.CURRENT_PRICE_KEYS,
            )

            if current is not None:

                currency = self._extract_currency(
                    data
                )

                regular_price = (
                    self._find_price_by_keys(
                        data,
                        self.REGULAR_PRICE_KEYS,
                    )
                )

                return {
                    "price": current,
                    "currency": currency,
                    "price_known": True,
                    "price_source": "structured_current",
                    "regular_price": regular_price,
                    "regular_price_known":
                        regular_price is not None,
                }

            # Schema.org / Offer часто использует
            # priceSpecification.
            price_specification = self._find_nested_key(
                data,
                "priceSpecification",
            )

            if price_specification is not None:

                nested = self._extract_structured_price(
                    price_specification
                )

                if nested["price"] is not None:
                    return nested

            # Offers могут быть dict/list.
            offers = self._find_nested_key(
                data,
                "offers",
            )

            if offers is not None:

                nested = self._extract_structured_price(
                    offers
                )

                if nested["price"] is not None:
                    return nested

            # Затем рекурсивно проверяем вложенные
            # структуры JSON-LD.
            for key, value in data.items():

                if key in {
                    "offers",
                    "priceSpecification",
                    "price",
                    "currentPrice",
                    "salePrice",
                }:
                    continue

                nested = self._extract_structured_price(
                    value
                )

                if nested["price"] is not None:
                    return nested

        elif isinstance(data, list):

            for item in data:

                nested = self._extract_structured_price(
                    item
                )

                if nested["price"] is not None:
                    return nested

        return result

    # =========================================================
    # COMMERCIAL FIELDS
    # =========================================================

    def _extract_commercial_fields(
        self,
        data: Any,
    ) -> dict[str, Any]:

        result = self._empty_result()

        if not isinstance(data, dict):
            return result

        normalized_keys = {
            self._normalize_key(key): key
            for key in data.keys()
        }

        # Текущая цена.
        for key in self.CURRENT_PRICE_KEYS:

            normalized = self._normalize_key(
                key
            )

            actual_key = normalized_keys.get(
                normalized
            )

            if actual_key is None:
                continue

            price = self._to_float(
                data.get(actual_key)
            )

            if price is None:
                continue

            return {
                "price": price,
                "currency": self._extract_currency(
                    data
                ),
                "price_known": True,
                "price_source": (
                    "commercial_"
                    + self._normalize_key(key)
                ),
                "regular_price": self._find_price_by_keys(
                    data,
                    self.REGULAR_PRICE_KEYS,
                ),
                "regular_price_known":
                    self._find_price_by_keys(
                        data,
                        self.REGULAR_PRICE_KEYS,
                    ) is not None,
            }

        # Meta / itemprop / data-* поля могут приходить
        # как обычный словарь.
        for key, value in data.items():

            normalized_key = self._normalize_key(
                key
            )

            if not self._looks_like_price_key(
                normalized_key
            ):
                continue

            if normalized_key in self.EXCLUDED_PRICE_KEYS:
                continue

            price = self._to_float(
                value
            )

            if price is None:
                continue

            return {
                "price": price,
                "currency": self._extract_currency(
                    data
                ),
                "price_known": True,
                "price_source": (
                    "commercial_attribute"
                ),
                "regular_price": None,
                "regular_price_known": False,
            }

        return result

    # =========================================================
    # GENERIC DATA
    # =========================================================

    def _extract_from_data(
        self,
        data: Any,
    ) -> dict[str, Any]:

        result = self._empty_result()

        if isinstance(data, dict):

            # Сначала строго проверяем текущую цену.
            current = self._find_price_by_keys(
                data,
                self.CURRENT_PRICE_KEYS,
            )

            if current is not None:

                return {
                    "price": current,
                    "currency": self._extract_currency(
                        data
                    ),
                    "price_known": True,
                    "price_source": "data_current",
                    "regular_price":
                        self._find_price_by_keys(
                            data,
                            self.REGULAR_PRICE_KEYS,
                        ),
                    "regular_price_known":
                        self._find_price_by_keys(
                            data,
                            self.REGULAR_PRICE_KEYS,
                        ) is not None,
                }

            # Затем generic amount/value.
            for key in self.GENERIC_PRICE_KEYS:

                if key not in data:
                    continue

                normalized_key = self._normalize_key(
                    key
                )

                if normalized_key in self.EXCLUDED_PRICE_KEYS:
                    continue

                value = self._to_float(
                    data.get(key)
                )

                if value is not None:

                    return {
                        "price": value,
                        "currency":
                            self._extract_currency(
                                data
                            ),
                        "price_known": True,
                        "price_source":
                            "data_generic",
                        "regular_price": None,
                        "regular_price_known": False,
                    }

            # Рекурсивный поиск.
            for key, value in data.items():

                if (
                    self._normalize_key(key)
                    in self.EXCLUDED_PRICE_KEYS
                ):
                    continue

                nested = self._extract_from_data(
                    value
                )

                if nested["price"] is not None:
                    return nested

        elif isinstance(data, list):

            for item in data:

                nested = self._extract_from_data(
                    item
                )

                if nested["price"] is not None:
                    return nested

        return result

    # =========================================================
    # TEXT
    # =========================================================

    def _extract_from_text(
        self,
        text: str,
    ) -> dict[str, Any]:

        result = self._empty_result()

        if not text:
            return result

        # Убираем чрезмерные пробелы,
        # но сохраняем разделители валюты.
        normalized_text = re.sub(
            r"\s+",
            " ",
            text,
        ).strip()

        patterns = [
            # $1,299.99
            (
                r"([$€£₽₴])\s*"
                r"(\d[\d\s,]*(?:\.\d+)?)"
            ),

            # 1,299.99 USD
            (
                r"(\d[\d\s,]*(?:\.\d+)?)\s*"
                r"(USD|EUR|GBP|RUB|BYN|PLN|CNY|UAH)\b"
            ),

            # 1 299,99 €
            (
                r"(\d[\d\s.,]*)\s*"
                r"([$€£₽₴]|zł)"
            ),

            # 1 299 руб.
            (
                r"(\d[\d\s.,]*)\s*"
                r"(руб\.?|рублей|евро|долларов|"
                r"долл\.?|фунтов?|злотых?)"
            ),
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                normalized_text,
                flags=re.IGNORECASE,
            )

            if not match:
                continue

            groups = match.groups()

            if len(groups) != 2:
                continue

            first = groups[0]
            second = groups[1]

            # Currency first.
            if (
                first in self.CURRENCY_SYMBOLS
            ):

                currency = (
                    self.CURRENCY_SYMBOLS[first]
                )

                price = self._to_float(
                    second
                )

            # Currency after price.
            else:

                price = self._to_float(
                    first
                )

                currency = (
                    self._normalize_currency(
                        second
                    )
                )

            if price is None:
                continue

            return {
                "price": price,
                "currency": currency,
                "price_known": True,
                "price_source": "text",
                "regular_price": None,
                "regular_price_known": False,
            }

        return result

    # =========================================================
    # HELPERS
    # =========================================================

    def _find_price_by_keys(
        self,
        data: dict[str, Any],
        keys: tuple[str, ...],
    ) -> float | None:

        normalized_keys = {
            self._normalize_key(key): key
            for key in data.keys()
        }

        for key in keys:

            normalized = self._normalize_key(
                key
            )

            actual_key = normalized_keys.get(
                normalized
            )

            if actual_key is None:
                continue

            value = self._to_float(
                data.get(actual_key)
            )

            if value is not None:
                return value

        return None

    def _find_nested_key(
        self,
        data: Any,
        target_key: str,
    ) -> Any:

        normalized_target = self._normalize_key(
            target_key
        )

        if isinstance(data, dict):

            for key, value in data.items():

                if (
                    self._normalize_key(key)
                    == normalized_target
                ):
                    return value

            for value in data.values():

                result = self._find_nested_key(
                    value,
                    target_key,
                )

                if result is not None:
                    return result

        elif isinstance(data, list):

            for item in data:

                result = self._find_nested_key(
                    item,
                    target_key,
                )

                if result is not None:
                    return result

        return None

    def _extract_currency(
        self,
        data: Any,
    ) -> str | None:

        if isinstance(data, dict):

            # Сначала стандартные currency keys.
            for key in self.CURRENCY_KEYS:

                normalized_key = self._normalize_key(
                    key
                )

                for actual_key, value in data.items():

                    if (
                        self._normalize_key(
                            actual_key
                        )
                        != normalized_key
                    ):
                        continue

                    currency = (
                        self._normalize_currency(
                            value
                        )
                    )

                    if currency:
                        return currency

            # Затем рекурсивный поиск.
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

        # Частые текстовые варианты.
        aliases = {
            "dollar": "USD",
            "dollars": "USD",
            "доллар": "USD",
            "долларов": "USD",
            "долл": "USD",
            "евро": "EUR",
            "руб": "RUB",
            "руб.": "RUB",
            "рублей": "RUB",
            "фунт": "GBP",
            "фунтов": "GBP",
            "злотый": "PLN",
            "злотых": "PLN",
        }

        return aliases.get(
            normalized
        )

    def _looks_like_price_key(
        self,
        key: str,
    ) -> bool:

        if not key:
            return False

        normalized = self._normalize_key(
            key
        )

        if normalized in self.EXCLUDED_PRICE_KEYS:
            return False

        price_markers = (
            "price",
            "saleprice",
            "currentprice",
            "offerprice",
            "sellingprice",
            "finalprice",
            "discountprice",
            "amount",
        )

        return any(
            marker in normalized
            for marker in price_markers
        )

    @staticmethod
    def _normalize_key(
        key: Any,
    ) -> str:

        return re.sub(
            r"[^a-z0-9]",
            "",
            str(key).lower(),
        )

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

            if not text:
                return None

            # Удаляем валютные символы,
            # но оставляем цифры и разделители.
            text = re.sub(
                r"[^\d,.\-]",
                "",
                text,
            )

            if not text:
                return None

            # 1,299.99
            # 1.299,99
            if (
                "," in text
                and "." in text
            ):

                if (
                    text.rfind(",")
                    <
                    text.rfind(".")
                ):

                    text = text.replace(
                        ",",
                        "",
                    )

                else:

                    text = (
                        text.replace(
                            ".",
                            "",
                        )
                        .replace(
                            ",",
                            ".",
                        )
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

            # 1.299
            #
            # Не считаем точку разделителем тысяч
            # автоматически, потому что 1.299 может
            # означать 1.299.
            elif "." in text:

                parts = text.split(".")

                if (
                    len(parts) == 2
                    and len(parts[1]) == 3
                    and parts[0].isdigit()
                    and parts[1].isdigit()
                ):
                    # Для коммерческой цены значение
                    # вида 1.299 чаще является
                    # разделителем тысяч.
                    text = (
                        parts[0]
                        + parts[1]
                    )

            return float(text)

        except (
            TypeError,
            ValueError,
        ):
            return None