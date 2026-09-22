import json
from typing import Any
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup


class OfferExtractor:
    """
    Универсальный extractor товарных страниц.

    Извлекает:
    - название;
    - бренд;
    - цену;
    - валюту;
    - описание;
    - изображение;
    - продавца;
    - наличие;
    - конечный URL.
    """

    name = "offer_extractor"

    def __init__(
        self,
        timeout: int = 15,
    ):
        self.timeout = timeout

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

            json_ld = self._extract_json_ld(
                soup
            )

            product_data = self._find_product(
                json_ld
            )

            offer_data = self._find_offer(
                product_data
            )

            title = (
                self._clean(
                    product_data.get("name")
                )
                or self._meta(
                    soup,
                    "og:title",
                )
                or self._clean(
                    fallback.get("title")
                )
            )

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
                    fallback.get("description")
                )
            )

            brand = self._extract_brand(
                product_data
            )

            price = self._extract_price(
                offer_data
            )

            currency = (
                self._clean(
                    offer_data.get(
                        "priceCurrency"
                    )
                )
                or self._extract_meta_currency(
                    soup
                )
                or fallback.get(
                    "currency"
                )
            )

            seller = self._extract_seller(
                offer_data
            )

            availability = (
                self._clean(
                    offer_data.get(
                        "availability"
                    )
                )
                or fallback.get(
                    "availability"
                )
                or "unknown"
            )

            image = self._extract_image(
                product_data
            )

            if not image:
                image = self._meta(
                    soup,
                    "og:image",
                )

            domain = urlparse(
                final_url
            ).netloc

            return {
                "title": title,
                "brand": brand,
                "price": price,
                "currency": currency,
                "description": description,
                "image": image,
                "seller": seller,
                "availability": availability,
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
        }

    def _extract_json_ld(
        self,
        soup: BeautifulSoup,
    ) -> list[Any]:

        results = []

        scripts = soup.find_all(
            "script",
            type="application/ld+json",
        )

        for script in scripts:

            raw = script.string

            if not raw:
                raw = script.get_text(
                    strip=True
                )

            if not raw:
                continue

            try:
                data = json.loads(
                    raw
                )

            except Exception:
                continue

            if isinstance(
                data,
                list,
            ):
                results.extend(
                    data
                )
            else:
                results.append(
                    data
                )

        return results

    def _find_product(
        self,
        data: list[Any],
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

            for value in item.values():

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

                if isinstance(
                    offer,
                    dict,
                ):
                    return offer

        return {}

    def _extract_price(
        self,
        offer: dict[str, Any],
    ):

        if not offer:
            return None

        price = offer.get(
            "price"
        )

        if price is None:
            price = offer.get(
                "lowPrice"
            )

        if price is None:
            price = offer.get(
                "highPrice"
            )

        if price is None:
            return None

        try:
            return float(
                str(price)
                .replace(",", ".")
                .strip()
            )

        except (
            TypeError,
            ValueError,
        ):
            return None

    def _extract_brand(
        self,
        product: dict[str, Any],
    ):

        brand = product.get(
            "brand"
        )

        if isinstance(
            brand,
            dict,
        ):

            return self._clean(
                brand.get("name")
            )

        return self._clean(
            brand
        )

    def _extract_seller(
        self,
        offer: dict[str, Any],
    ):

        seller = offer.get(
            "seller"
        )

        if isinstance(
            seller,
            dict,
        ):

            return self._clean(
                seller.get("name")
            )

        return self._clean(
            seller
        )

    def _extract_image(
        self,
        product: dict[str, Any],
    ):

        image = product.get(
            "image"
        )

        if isinstance(
            image,
            list,
        ):

            if image:
                return image[0]

            return None

        if isinstance(
            image,
            dict,
        ):

            return (
                image.get("url")
                or image.get("contentUrl")
            )

        return image

    @staticmethod
    def _meta(
        soup: BeautifulSoup,
        property_name: str,
    ):

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
    ):

        candidates = [
            "product:price:currency",
            "og:price:currency",
        ]

        for candidate in candidates:

            value = self._meta(
                soup,
                candidate,
            )

            if value:
                return value.strip().upper()

        return None

    @staticmethod
    def _clean(
        value,
    ):

        if value is None:
            return None

        if isinstance(
            value,
            str,
        ):

            value = value.strip()

            return value or None

        return str(
            value
        ).strip() or None

    @staticmethod
    def _fallback_result(
        fallback: dict[str, Any],
        url: str | None = None,
    ):

        return {
            "title":
                fallback.get("title"),

            "brand":
                fallback.get("brand"),

            "price":
                fallback.get("price"),

            "currency":
                fallback.get("currency"),

            "description":
                fallback.get("description"),

            "image":
                fallback.get("image"),

            "seller":
                fallback.get("seller"),

            "availability":
                fallback.get(
                    "availability",
                    "unknown",
                ),

            "url":
                url
                or fallback.get("url"),

            "domain":
                fallback.get("domain"),

            "extracted":
                False,
        }