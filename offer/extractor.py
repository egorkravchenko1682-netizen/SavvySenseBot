from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from .extraction import (
    AttributeExtractor,
    AvailabilityExtractor,
    ConditionExtractor,
    PriceExtractor,
    ProductExtractor,
    StructuredDataExtractor,
)


class OfferExtractor:
    """
    Универсальный extractor товарных страниц SAVVY SENSE.

    Архитектура:

        HTML
          ↓
        StructuredDataExtractor
          ↓
        ProductExtractor
        AttributeExtractor
        PriceExtractor
        ConditionExtractor
        AvailabilityExtractor
          ↓
        единый OfferExtractor result

    Публичный контракт сохраняется:

        extract(url, fallback) -> dict

    Поэтому существующий orchestrator менять не требуется.
    """

    name = "offer_extractor"

    def __init__(
        self,
        timeout: int = 15,
    ):
        self.timeout = timeout

        self.structured_data_extractor = (
            StructuredDataExtractor()
        )

        self.product_extractor = (
            ProductExtractor()
        )

        self.attribute_extractor = (
            AttributeExtractor()
        )

        self.price_extractor = (
            PriceExtractor()
        )

        self.condition_extractor = (
            ConditionExtractor()
        )

        self.availability_extractor = (
            AvailabilityExtractor()
        )

    # =========================================================
    # PUBLIC API
    # =========================================================

    def extract(
        self,
        url: str,
        fallback: dict[str, Any] | None = None,
    ) -> dict[str, Any]:

        fallback = fallback or {}

        if not url:
            return self._fallback_result(
                fallback
            )

        try:

            response = requests.get(
                url,
                headers=self._headers(),
                timeout=self.timeout,
                allow_redirects=True,
            )

            response.raise_for_status()

            final_url = response.url

            soup = BeautifulSoup(
                response.text,
                "html.parser",
            )

            # =================================================
            # STRUCTURED DATA
            # =================================================

            structured_objects = (
                self.structured_data_extractor.extract(
                    response.text
                )
            )

            product_data = (
                self._find_product(
                    structured_objects
                )
            )

            offer_data = (
                self._find_offer(
                    product_data
                )
            )

            # =================================================
            # PRODUCT
            # =================================================

            product_extracted = (
                self.product_extractor.extract(
                    data=product_data,
                    text=self._page_text(
                        soup
                    ),
                )
            )

            title = (
                product_extracted.get(
                    "title"
                )
                or self._meta(
                    soup,
                    "og:title",
                )
                or self._meta(
                    soup,
                    "twitter:title",
                )
                or self._clean(
                    fallback.get(
                        "title"
                    )
                )
            )

            brand = (
                product_extracted.get(
                    "brand"
                )
                or self._clean(
                    fallback.get(
                        "brand"
                    )
                )
            )

            model = (
                product_extracted.get(
                    "model"
                )
                or self._clean(
                    fallback.get(
                        "model"
                    )
                )
            )

            product_type = (
                product_extracted.get(
                    "product_type"
                )
                or self._clean(
                    fallback.get(
                        "product_type"
                    )
                )
            )

            category = (
                product_extracted.get(
                    "category"
                )
                or self._clean(
                    fallback.get(
                        "category"
                    )
                )
            )

            # =================================================
            # DESCRIPTION
            # =================================================

            description = (
                self._clean(
                    product_data.get(
                        "description"
                    )
                )
                or self._meta(
                    soup,
                    "og:description",
                )
                or self._clean(
                    fallback.get(
                        "description"
                    )
                )
            )

            # =================================================
            # ATTRIBUTES
            # =================================================

            page_text = self._page_text(
                soup
            )

            attributes = (
                self.attribute_extractor.extract(
                    data=product_data,
                    text=(
                        f"{title or ''} "
                        f"{description or ''} "
                        f"{page_text}"
                    ),
                )
            )

            fallback_attributes = (
                fallback.get(
                    "attributes",
                    {},
                )
            )

            if isinstance(
                fallback_attributes,
                dict,
            ):

                for key, value in (
                    fallback_attributes.items()
                ):

                    if (
                        key not in attributes
                        and value is not None
                    ):
                        attributes[key] = value

            # =================================================
            # PRICE
            # =================================================

            price_result = (
                self.price_extractor.extract(
                    data=offer_data,
                    text=(
                        f"{title or ''} "
                        f"{description or ''} "
                        f"{page_text}"
                    ),
                )
            )

            price = price_result.get(
                "price"
            )

            if price is None:
                meta_price = (
                    self._extract_meta_price(
                        soup
                    )
                )

                if meta_price is not None:
                    price = meta_price

            if price is None:
                price = (
                    self._clean_numeric_price(
                        fallback.get(
                            "price"
                        )
                    )
                )

            # =================================================
            # CURRENCY
            # =================================================

            currency = (
                price_result.get(
                    "currency"
                )
                or self._extract_meta_currency(
                    soup
                )
                or self._clean(
                    fallback.get(
                        "currency"
                    )
                )
            )

            if currency:
                currency = str(
                    currency
                ).upper()

            # =================================================
            # CONDITION
            # =================================================

            condition = (
                self.condition_extractor.extract(
                    data={
                        "product": product_data,
                        "offer": offer_data,
                    },
                    text=(
                        f"{title or ''} "
                        f"{description or ''} "
                        f"{page_text}"
                    ),
                )
            )

            if (
                condition == "unknown"
                and fallback.get(
                    "condition"
                )
            ):
                condition = self._clean(
                    fallback.get(
                        "condition"
                    )
                )

            attributes["condition"] = (
                condition
            )

            # =================================================
            # AVAILABILITY
            # =================================================

            availability = (
                self.availability_extractor.extract(
                    data={
                        "product": product_data,
                        "offer": offer_data,
                    },
                    text=(
                        f"{title or ''} "
                        f"{description or ''} "
                        f"{page_text}"
                    ),
                )
            )

            if (
                availability == "unknown"
                and fallback.get(
                    "availability"
                )
            ):
                availability = self._clean(
                    fallback.get(
                        "availability"
                    )
                )

            # =================================================
            # SELLER
            # =================================================

            seller = (
                self._extract_seller(
                    offer_data
                )
                or self._clean(
                    fallback.get(
                        "seller"
                    )
                )
                or self._domain_as_seller(
                    final_url
                )
            )

            # =================================================
            # IDENTIFIERS
            # =================================================

            sku = (
                product_extracted.get(
                    "sku"
                )
                or self._clean(
                    fallback.get(
                        "sku"
                    )
                )
            )

            mpn = (
                product_extracted.get(
                    "mpn"
                )
                or self._clean(
                    fallback.get(
                        "mpn"
                    )
                )
            )

            gtin = (
                product_extracted.get(
                    "gtin"
                )
                or self._clean(
                    fallback.get(
                        "gtin"
                    )
                )
            )

            # =================================================
            # IMAGE
            # =================================================

            image = self._extract_image(
                product_data
            )

            if not image:
                image = self._meta(
                    soup,
                    "og:image",
                )

            if not image:
                image = self._clean(
                    fallback.get(
                        "image"
                    )
                )

            # =================================================
            # DOMAIN
            # =================================================

            domain = urlparse(
                final_url
            ).netloc

            # =================================================
            # RESULT
            # =================================================

            return {
                "title": title,
                "brand": brand,
                "model": model,
                "product_type": product_type,
                "category": category,

                "attributes": attributes,

                "storage": attributes.get(
                    "storage"
                ),
                "color": attributes.get(
                    "color"
                ),
                "size": attributes.get(
                    "size"
                ),
                "material": attributes.get(
                    "material"
                ),
                "gender": attributes.get(
                    "gender"
                ),
                "condition": condition,

                "price": price,
                "currency": currency,

                "description": description,
                "image": image,

                "seller": seller,
                "availability": availability,

                "sku": sku,
                "mpn": mpn,
                "gtin": gtin,

                "url": final_url,
                "domain": domain,

                "extracted": True,
            }

        except Exception as error:

            print(
                f"Offer extraction failed "
                f"for {url}: {error}"
            )

            return self._fallback_result(
                fallback,
                url=url,
            )

    # =========================================================
    # HTTP
    # =========================================================

    @staticmethod
    def _headers():

        return {
            "User-Agent": (
                "Mozilla/5.0 "
                "(Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/126.0 Safari/537.36"
            ),
            "Accept-Language":
                "en-US,en;q=0.9",
            "Accept":
                "text/html,"
                "application/xhtml+xml,"
                "application/xml;q=0.9,"
                "*/*;q=0.8",
            "Cache-Control":
                "no-cache",
        }

    # =========================================================
    # PRODUCT FINDER
    # =========================================================

    def _find_product(
        self,
        data: list[dict[str, Any]],
    ) -> dict[str, Any]:

        for item in data:

            found = (
                self._find_product_recursive(
                    item
                )
            )

            if found:
                return found

        return {}

    def _find_product_recursive(
        self,
        item: Any,
    ) -> dict[str, Any]:

        if isinstance(
            item,
            dict,
        ):

            item_type = item.get(
                "@type"
            )

            if isinstance(
                item_type,
                list,
            ):

                types = [
                    str(value).lower()
                    for value in item_type
                ]

            else:

                types = [
                    str(
                        item_type
                    ).lower()
                ]

            if (
                "product" in types
                or "productgroup" in types
                or any(
                    value.endswith(
                        "/product"
                    )
                    for value in types
                )
            ):
                return item

            graph = item.get(
                "@graph"
            )

            if isinstance(
                graph,
                list,
            ):

                for child in graph:

                    found = (
                        self._find_product_recursive(
                            child
                        )
                    )

                    if found:
                        return found

            for key in (
                "mainEntity",
                "mainEntityOfPage",
                "item",
                "subjectOf",
            ):

                nested = item.get(
                    key
                )

                if nested is not None:

                    found = (
                        self._find_product_recursive(
                            nested
                        )
                    )

                    if found:
                        return found

            for value in item.values():

                if isinstance(
                    value,
                    (
                        dict,
                        list,
                    ),
                ):

                    found = (
                        self._find_product_recursive(
                            value
                        )
                    )

                    if found:
                        return found

        elif isinstance(
            item,
            list,
        ):

            for child in item:

                found = (
                    self._find_product_recursive(
                        child
                    )
                )

                if found:
                    return found

        return {}

    # =========================================================
    # OFFER
    # =========================================================

    def _find_offer(
        self,
        product: dict[str, Any],
    ) -> dict[str, Any]:

        offers = product.get(
            "offers"
        )

        if isinstance(
            offers,
            dict,
        ):
            return offers

        if isinstance(
            offers,
            list,
        ):

            for offer in offers:

                if not isinstance(
                    offer,
                    dict,
                ):
                    continue

                if (
                    offer.get(
                        "price"
                    ) is not None
                    or offer.get(
                        "lowPrice"
                    ) is not None
                ):
                    return offer

            for offer in offers:

                if isinstance(
                    offer,
                    dict,
                ):
                    return offer

        return {}

    # =========================================================
    # PRICE FALLBACK
    # =========================================================

    def _extract_meta_price(
        self,
        soup: BeautifulSoup,
    ) -> float | None:

        candidates = (
            "product:price:amount",
            "og:price:amount",
            "product:price",
            "price",
        )

        for candidate in candidates:

            value = self._meta(
                soup,
                candidate,
            )

            price = (
                self._clean_numeric_price(
                    value
                )
            )

            if price is not None:
                return price

        element = soup.find(
            attrs={
                "itemprop": "price"
            }
        )

        if element:

            value = (
                element.get(
                    "content"
                )
                or element.get_text(
                    strip=True
                )
            )

            price = (
                self._clean_numeric_price(
                    value
                )
            )

            if price is not None:
                return price

        return None

    @staticmethod
    def _clean_numeric_price(
        value: Any,
    ) -> float | None:

        if value is None:
            return None

        if isinstance(
            value,
            bool,
        ):
            return None

        if isinstance(
            value,
            (
                int,
                float,
            ),
        ):
            return float(
                value
            )

        text = str(
            value
        ).strip()

        if not text:
            return None

        text = (
            text
            .replace(
                "\xa0",
                " ",
            )
            .replace(
                " ",
                "",
            )
        )

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
                    text
                    .replace(
                        ".",
                        "",
                    )
                    .replace(
                        ",",
                        ".",
                    )
                )

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

        match = re.search(
            r"-?\d+(?:\.\d+)?",
            text,
        )

        if not match:
            return None

        try:

            return float(
                match.group(0)
            )

        except (
            TypeError,
            ValueError,
        ):

            return None

    # =========================================================
    # SELLER
    # =========================================================

    def _extract_seller(
        self,
        offer: dict[str, Any],
    ) -> str | None:

        seller = offer.get(
            "seller"
        )

        if isinstance(
            seller,
            dict,
        ):

            return self._clean(
                seller.get(
                    "name"
                )
            )

        return self._clean(
            seller
        )

    @staticmethod
    def _domain_as_seller(
        url: str,
    ) -> str | None:

        domain = urlparse(
            url
        ).netloc.lower()

        if domain.startswith(
            "www."
        ):
            domain = domain[4:]

        return domain or None

    # =========================================================
    # IMAGE
    # =========================================================

    def _extract_image(
        self,
        product: dict[str, Any],
    ) -> str | None:

        image = product.get(
            "image"
        )

        if isinstance(
            image,
            list,
        ):

            if not image:
                return None

            first = image[0]

            if isinstance(
                first,
                dict,
            ):

                return (
                    first.get(
                        "url"
                    )
                    or first.get(
                        "contentUrl"
                    )
                )

            return self._clean(
                first
            )

        if isinstance(
            image,
            dict,
        ):

            return (
                image.get(
                    "url"
                )
                or image.get(
                    "contentUrl"
                )
            )

        return self._clean(
            image
        )

    # =========================================================
    # META
    # =========================================================

    @staticmethod
    def _meta(
        soup: BeautifulSoup,
        property_name: str,
    ) -> str | None:

        element = soup.find(
            "meta",
            attrs={
                "property":
                    property_name
            },
        )

        if not element:

            element = soup.find(
                "meta",
                attrs={
                    "name":
                        property_name
                },
            )

        if not element:
            return None

        return element.get(
            "content"
        )

    def _extract_meta_currency(
        self,
        soup: BeautifulSoup,
    ) -> str | None:

        candidates = (
            "product:price:currency",
            "og:price:currency",
            "priceCurrency",
        )

        for candidate in candidates:

            value = self._meta(
                soup,
                candidate,
            )

            if value:
                return (
                    str(value)
                    .strip()
                    .upper()
                )

        element = soup.find(
            attrs={
                "itemprop":
                    "priceCurrency"
            }
        )

        if element:

            value = (
                element.get(
                    "content"
                )
                or element.get_text(
                    strip=True
                )
            )

            if value:
                return (
                    str(value)
                    .strip()
                    .upper()
                )

        return None

    # =========================================================
    # PAGE TEXT
    # =========================================================

    @staticmethod
    def _page_text(
        soup: BeautifulSoup,
    ) -> str:

        for element in soup(
            [
                "script",
                "style",
                "noscript",
            ]
        ):
            element.decompose()

        text = soup.get_text(
            " ",
            strip=True,
        )

        return re.sub(
            r"\s+",
            " ",
            text,
        ).strip()

    # =========================================================
    # CLEAN
    # =========================================================

    @staticmethod
    def _clean(
        value: Any,
    ) -> str | None:

        if value is None:
            return None

        if isinstance(
            value,
            str,
        ):

            value = (
                value
                .replace(
                    "\xa0",
                    " ",
                )
                .strip()
            )

            return value or None

        return str(
            value
        ).strip() or None

    # =========================================================
    # FALLBACK
    # =========================================================

    @staticmethod
    def _fallback_result(
        fallback: dict[str, Any],
        url: str | None = None,
    ) -> dict[str, Any]:

        attributes = fallback.get(
            "attributes",
            {},
        )

        if not isinstance(
            attributes,
            dict,
        ):
            attributes = {}

        condition = (
            fallback.get(
                "condition"
            )
            or attributes.get(
                "condition"
            )
            or "unknown"
        )

        return {
            "title":
                fallback.get(
                    "title"
                ),

            "brand":
                fallback.get(
                    "brand"
                ),

            "model":
                fallback.get(
                    "model"
                ),

            "product_type":
                fallback.get(
                    "product_type"
                ),

            "category":
                fallback.get(
                    "category"
                ),

            "attributes":
                attributes,

            "storage":
                fallback.get(
                    "storage"
                )
                or attributes.get(
                    "storage"
                ),

            "color":
                fallback.get(
                    "color"
                )
                or attributes.get(
                    "color"
                ),

            "size":
                fallback.get(
                    "size"
                )
                or attributes.get(
                    "size"
                ),

            "material":
                fallback.get(
                    "material"
                )
                or attributes.get(
                    "material"
                ),

            "gender":
                fallback.get(
                    "gender"
                )
                or attributes.get(
                    "gender"
                ),

            "condition":
                condition,

            "price":
                fallback.get(
                    "price"
                ),

            "currency":
                fallback.get(
                    "currency"
                ),

            "description":
                fallback.get(
                    "description"
                ),

            "image":
                fallback.get(
                    "image"
                ),

            "seller":
                fallback.get(
                    "seller"
                ),

            "availability":
                fallback.get(
                    "availability",
                    "unknown",
                ),

            "sku":
                fallback.get(
                    "sku"
                ),

            "mpn":
                fallback.get(
                    "mpn"
                ),

            "gtin":
                fallback.get(
                    "gtin"
                ),

            "url":
                url
                or fallback.get(
                    "url"
                ),

            "domain":
                fallback.get(
                    "domain"
                ),

            "extracted":
                False,
        }