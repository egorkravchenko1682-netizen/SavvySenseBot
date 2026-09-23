from __future__ import annotations

import json
from typing import Any


class StructuredDataExtractor:
    """
    Извлекает структурированные данные из HTML.

    Основной источник:
    JSON-LD <script type="application/ld+json">

    Модуль не извлекает отдельные поля товара.
    Он только находит и нормализует структурированные
    объекты, которые затем обрабатываются другими
    extractor-модулями.
    """

    def extract(
        self,
        html: str | None = None,
    ) -> list[dict[str, Any]]:

        if not html:
            return []

        scripts = self._extract_json_ld_blocks(
            html
        )

        if not scripts:
            return []

        objects: list[dict[str, Any]] = []

        for script in scripts:

            parsed = self._parse_json(
                script
            )

            if parsed is None:
                continue

            objects.extend(
                self._flatten_objects(
                    parsed
                )
            )

        return objects

    def extract_products(
        self,
        html: str | None = None,
    ) -> list[dict[str, Any]]:

        objects = self.extract(
            html
        )

        products = []

        for obj in objects:

            if self._is_product(
                obj
            ):
                products.append(
                    obj
                )

        return products

    def extract_offers(
        self,
        html: str | None = None,
    ) -> list[dict[str, Any]]:

        objects = self.extract(
            html
        )

        offers = []

        for obj in objects:

            if self._is_offer(
                obj
            ):
                offers.append(
                    obj
                )

        return offers

    def find_product(
        self,
        html: str | None = None,
    ) -> dict[str, Any] | None:

        products = self.extract_products(
            html
        )

        if products:
            return products[0]

        return None

    def find_offer(
        self,
        html: str | None = None,
    ) -> dict[str, Any] | None:

        offers = self.extract_offers(
            html
        )

        if offers:
            return offers[0]

        return None

    def _extract_json_ld_blocks(
        self,
        html: str,
    ) -> list[str]:

        blocks: list[str] = []

        lower_html = html.lower()

        marker = (
            '<script'
        )

        position = 0

        while True:

            start = lower_html.find(
                marker,
                position,
            )

            if start == -1:
                break

            end_tag = lower_html.find(
                ">",
                start,
            )

            if end_tag == -1:
                break

            opening_tag = lower_html[
                start:end_tag + 1
            ]

            if (
                "application/ld+json"
                not in opening_tag
            ):
                position = end_tag + 1
                continue

            closing_tag = lower_html.find(
                "</script>",
                end_tag + 1,
            )

            if closing_tag == -1:
                break

            content = html[
                end_tag + 1:
                closing_tag
            ]

            content = content.strip()

            if content:
                blocks.append(
                    content
                )

            position = (
                closing_tag
                + len("</script>")
            )

        return blocks

    def _parse_json(
        self,
        content: str,
    ) -> Any:

        if not content:
            return None

        content = content.strip()

        try:
            return json.loads(
                content
            )

        except json.JSONDecodeError:

            # Некоторые сайты добавляют
            # лишние символы вокруг JSON.
            cleaned = (
                content
                .strip()
                .strip("\ufeff")
            )

            try:
                return json.loads(
                    cleaned
                )
            except (
                json.JSONDecodeError,
                TypeError,
                ValueError,
            ):
                return None

    def _flatten_objects(
        self,
        value: Any,
    ) -> list[dict[str, Any]]:

        objects: list[dict[str, Any]] = []

        if isinstance(value, dict):

            objects.append(
                value
            )

            for key, child in value.items():

                if key in (
                    "@graph",
                    "itemListElement",
                    "offers",
                    "hasVariant",
                    "mainEntity",
                    "mainEntityOfPage",
                ):
                    objects.extend(
                        self._flatten_objects(
                            child
                        )
                    )

        elif isinstance(value, list):

            for item in value:

                objects.extend(
                    self._flatten_objects(
                        item
                    )
                )

        return objects

    def _is_product(
        self,
        data: dict[str, Any],
    ) -> bool:

        types = self._extract_types(
            data
        )

        for value in types:

            normalized = (
                value
                .lower()
                .strip()
            )

            if normalized == "product":
                return True

            if normalized.endswith(
                "/product"
            ):
                return True

        return False

    def _is_offer(
        self,
        data: dict[str, Any],
    ) -> bool:

        types = self._extract_types(
            data
        )

        for value in types:

            normalized = (
                value
                .lower()
                .strip()
            )

            if normalized == "offer":
                return True

            if normalized.endswith(
                "/offer"
            ):
                return True

        # Иногда сайты не указывают @type,
        # но объект явно является Offer.
        return any(
            key in data
            for key in (
                "price",
                "priceCurrency",
                "availability",
                "itemCondition",
            )
        )

    def _extract_types(
        self,
        data: dict[str, Any],
    ) -> list[str]:

        value = data.get(
            "@type"
        )

        if value is None:
            return []

        if isinstance(
            value,
            str,
        ):
            return [value]

        if isinstance(
            value,
            list,
        ):
            return [
                str(item)
                for item in value
                if item is not None
            ]

        return [
            str(value)
        ]

    @staticmethod
    def get_product_offers(
        product: dict[str, Any],
    ) -> list[dict[str, Any]]:

        offers = product.get(
            "offers"
        )

        if offers is None:
            return []

        if isinstance(
            offers,
            dict,
        ):
            return [offers]

        if isinstance(
            offers,
            list,
        ):
            return [
                item
                for item in offers
                if isinstance(
                    item,
                    dict,
                )
            ]

        return []

    @staticmethod
    def get_brand_name(
        product: dict[str, Any],
    ) -> str | None:

        brand = product.get(
            "brand"
        )

        if isinstance(
            brand,
            str,
        ):
            return brand.strip() or None

        if isinstance(
            brand,
            dict,
        ):
            name = brand.get(
                "name"
            )

            if name:
                return str(
                    name
                ).strip()

        return None

    @staticmethod
    def get_product_name(
        product: dict[str, Any],
    ) -> str | None:

        for key in (
            "name",
            "headline",
            "title",
        ):

            value = product.get(
                key
            )

            if value:

                return str(
                    value
                ).strip()

        return None