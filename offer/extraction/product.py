from __future__ import annotations

import re
from typing import Any


class ProductExtractor:
    """
    Извлекает идентичность товара.

    Ответственность модуля:
    - title
    - brand
    - model
    - product_type
    - category
    - SKU
    - MPN
    - GTIN / UPC / EAN

    Модуль не определяет:
    - цену
    - состояние
    - наличие
    - доставку
    """

    BRAND_KEYS = (
        "brand",
        "manufacturer",
        "brandName",
    )

    MODEL_KEYS = (
        "model",
        "modelName",
        "modelNumber",
    )

    PRODUCT_TYPE_KEYS = (
        "product_type",
        "productType",
        "type",
    )

    CATEGORY_KEYS = (
        "category",
        "productCategory",
        "categoryName",
    )

    TITLE_KEYS = (
        "title",
        "name",
        "productName",
        "headline",
    )

    SKU_KEYS = (
        "sku",
        "SKU",
        "productId",
        "itemId",
    )

    MPN_KEYS = (
        "mpn",
        "MPN",
        "manufacturerPartNumber",
        "partNumber",
    )

    GTIN_KEYS = (
        "gtin",
        "gtin8",
        "gtin12",
        "gtin13",
        "gtin14",
        "upc",
        "ean",
    )

    def extract(
        self,
        data: dict[str, Any] | None = None,
        text: str | None = None,
    ) -> dict[str, Any]:

        data = data or {}

        result = {
            "title": None,
            "brand": None,
            "model": None,
            "product_type": None,
            "category": None,
            "sku": None,
            "mpn": None,
            "gtin": None,
        }

        result["title"] = self._extract_first_value(
            data,
            self.TITLE_KEYS,
        )

        result["brand"] = self._extract_brand(
            data
        )

        result["model"] = self._extract_first_value(
            data,
            self.MODEL_KEYS,
        )

        result["product_type"] = (
            self._extract_first_value(
                data,
                self.PRODUCT_TYPE_KEYS,
            )
        )

        result["category"] = (
            self._extract_first_value(
                data,
                self.CATEGORY_KEYS,
            )
        )

        result["sku"] = self._extract_first_value(
            data,
            self.SKU_KEYS,
        )

        result["mpn"] = self._extract_first_value(
            data,
            self.MPN_KEYS,
        )

        result["gtin"] = self._extract_gtin(
            data
        )

        if text:
            result = self._fill_from_text(
                result,
                text,
            )

        result = self._normalize_result(
            result
        )

        return result

    def _extract_brand(
        self,
        data: Any,
    ) -> str | None:

        value = self._extract_first_value(
            data,
            self.BRAND_KEYS,
        )

        if isinstance(value, dict):
            value = (
                value.get("name")
                or value.get("@value")
            )

        if value:
            return str(value).strip()

        return None

    def _extract_gtin(
        self,
        data: Any,
    ) -> str | None:

        for key in self.GTIN_KEYS:

            value = self._find_key(
                data,
                key,
            )

            if value is None:
                continue

            if isinstance(value, dict):
                value = (
                    value.get("value")
                    or value.get("@value")
                )

            normalized = self._normalize_identifier(
                value
            )

            if normalized:
                return normalized

        return None

    def _fill_from_text(
        self,
        result: dict[str, Any],
        text: str,
    ) -> dict[str, Any]:

        if not text:
            return result

        text = str(text).strip()

        if not result.get("title"):
            result["title"] = text

        if not result.get("brand"):
            result["brand"] = (
                self._detect_brand_from_text(
                    text
                )
            )

        if not result.get("model"):
            result["model"] = (
                self._detect_model_from_text(
                    text
                )
            )

        if not result.get("product_type"):
            result["product_type"] = (
                self._detect_product_type(
                    text
                )
            )

        return result

    def _detect_brand_from_text(
        self,
        text: str,
    ) -> str | None:

        normalized = text.lower()

        brands = (
            "apple",
            "samsung",
            "xiaomi",
            "google",
            "oneplus",
            "huawei",
            "honor",
            "sony",
            "lg",
            "lenovo",
            "asus",
            "acer",
            "hp",
            "dell",
            "msi",
            "microsoft",
            "nike",
            "adidas",
            "puma",
            "reebok",
            "bosch",
            "philips",
            "dyson",
            "makita",
            "dewalt",
            "milwaukee",
            "ikea",
            "lego",
            "logitech",
            "jbl",
            "canon",
            "nikon",
            "fujifilm",
            "gopro",
            "dji",
            "roborock",
            "dreame",
            "ecovacs",
        )

        for brand in brands:

            if re.search(
                rf"\b{re.escape(brand)}\b",
                normalized,
            ):
                return brand

        markers = {
            "apple": (
                "iphone",
                "ipad",
                "macbook",
                "airpods",
                "apple watch",
            ),
            "samsung": (
                "galaxy",
            ),
            "google": (
                "pixel",
            ),
            "xiaomi": (
                "redmi",
                "poco",
            ),
            "sony": (
                "xperia",
                "playstation",
            ),
            "microsoft": (
                "surface",
                "xbox",
            ),
            "dyson": (
                "airwrap",
                "supersonic",
                "v15 detect",
            ),
        }

        for brand, brand_markers in markers.items():

            for marker in brand_markers:

                if re.search(
                    rf"\b{re.escape(marker)}\b",
                    normalized,
                ):
                    return brand

        return None

    def _detect_model_from_text(
        self,
        text: str,
    ) -> str | None:

        normalized = text.strip()

        # Apple iPhone
        match = re.search(
            r"\b(iPhone\s+"
            r"\d+"
            r"(?:\s+(?:Pro|Pro\s+Max|Plus|mini|Max))?"
            r"(?:\s+\w+)?)",
            normalized,
            flags=re.IGNORECASE,
        )

        if match:
            return self._clean_model(
                match.group(1)
            )

        # Samsung Galaxy
        match = re.search(
            r"\b(Galaxy\s+"
            r"(?:S|A|Z|Note)"
            r"\s*[\w\-]+"
            r"(?:\s+(?:Ultra|Plus|FE))?)",
            normalized,
            flags=re.IGNORECASE,
        )

        if match:
            return self._clean_model(
                match.group(1)
            )

        return None

    def _detect_product_type(
        self,
        text: str,
    ) -> str | None:

        normalized = text.lower()

        product_types = {
            "smartphone": (
                "iphone",
                "смартфон",
                "smartphone",
                "galaxy",
                "pixel",
            ),
            "laptop": (
                "ноутбук",
                "laptop",
                "macbook",
            ),
            "tablet": (
                "планшет",
                "tablet",
                "ipad",
            ),
            "headphones": (
                "наушники",
                "headphones",
                "earbuds",
                "airpods",
            ),
            "camera": (
                "камера",
                "camera",
                "фотоаппарат",
            ),
            "television": (
                "телевизор",
                "телевизор",
                "tv",
            ),
            "shoes": (
                "кроссовки",
                "обувь",
                "shoes",
                "sneakers",
            ),
            "clothing": (
                "куртка",
                "футболка",
                "рубашка",
                "брюки",
                "одежда",
                "jacket",
                "shirt",
                "clothing",
            ),
            "furniture": (
                "диван",
                "кровать",
                "стол",
                "стул",
                "мебель",
                "sofa",
                "bed",
                "table",
                "chair",
            ),
            "appliance": (
                "холодильник",
                "пылесос",
                "стиральная машина",
                "vacuum",
                "refrigerator",
                "washing machine",
            ),
            "tool": (
                "дрель",
                "шуруповерт",
                "перфоратор",
                "инструмент",
                "drill",
                "screwdriver",
                "tool",
            ),
        }

        for product_type, markers in product_types.items():

            for marker in markers:

                if re.search(
                    rf"\b{re.escape(marker)}\b",
                    normalized,
                ):
                    return product_type

        return None

    def _extract_first_value(
        self,
        data: Any,
        keys: tuple[str, ...],
    ) -> Any:

        if isinstance(data, dict):

            for key in keys:

                if key in data:

                    value = data.get(key)

                    if self._is_valid_value(
                        value
                    ):
                        return value

            for value in data.values():

                result = self._extract_first_value(
                    value,
                    keys,
                )

                if self._is_valid_value(
                    result
                ):
                    return result

        elif isinstance(data, list):

            for item in data:

                result = self._extract_first_value(
                    item,
                    keys,
                )

                if self._is_valid_value(
                    result
                ):
                    return result

        return None

    def _find_key(
        self,
        data: Any,
        key: str,
    ) -> Any:

        if isinstance(data, dict):

            if key in data:
                return data[key]

            for value in data.values():

                result = self._find_key(
                    value,
                    key,
                )

                if result is not None:
                    return result

        elif isinstance(data, list):

            for item in data:

                result = self._find_key(
                    item,
                    key,
                )

                if result is not None:
                    return result

        return None

    def _normalize_result(
        self,
        result: dict[str, Any],
    ) -> dict[str, Any]:

        for key in (
            "title",
            "brand",
            "model",
            "product_type",
            "category",
            "sku",
            "mpn",
        ):

            value = result.get(key)

            if value is None:
                continue

            if isinstance(value, dict):
                value = (
                    value.get("name")
                    or value.get("@value")
                    or value.get("value")
                )

            if value is None:
                result[key] = None
                continue

            result[key] = str(
                value
            ).strip()

            if not result[key]:
                result[key] = None

        if result.get("brand"):
            result["brand"] = (
                result["brand"]
                .lower()
                .strip()
            )

        if result.get("gtin"):
            result["gtin"] = (
                self._normalize_identifier(
                    result["gtin"]
                )
            )

        return result

    @staticmethod
    def _normalize_identifier(
        value: Any,
    ) -> str | None:

        if value is None:
            return None

        value = str(
            value
        ).strip()

        value = re.sub(
            r"[\s\-]",
            "",
            value,
        )

        return value or None

    @staticmethod
    def _clean_model(
        value: str,
    ) -> str:

        value = re.sub(
            r"\s+",
            " ",
            value,
        )

        return value.strip()

    @staticmethod
    def _is_valid_value(
        value: Any,
    ) -> bool:

        if value is None:
            return False

        if isinstance(value, str):
            return bool(value.strip())

        return True