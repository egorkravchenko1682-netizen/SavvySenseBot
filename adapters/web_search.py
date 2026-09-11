import json
import re
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

from products import Product
from adapters.base import ShopAdapter


class WebSearchAdapter(ShopAdapter):

    @property
    def shop_name(self) -> str:
        return "web"

    def can_handle(self, url: str) -> bool:
        return True

    def get_product(self, url: str) -> Product | None:
        return self.extract_product_page(url)

    def search(self, query: str) -> list[Product]:

        results = []

        search_url = "https://html.duckduckgo.com/html/"

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/125.0 Safari/537.36"
            )
        }

        try:

            response = requests.get(
                search_url,
                params={
                    "q": query,
                },
                headers=headers,
                timeout=15,
            )

            response.raise_for_status()

        except Exception as e:

            print(
                "Web search error:",
                e,
            )

            return []

        soup = BeautifulSoup(
            response.text,
            "html.parser",
        )

        links = soup.select(
            ".result__a"
        )

        for link in links[:10]:

            try:

                title = link.get_text(
                    " ",
                    strip=True,
                )

                url = link.get(
                    "href"
                )

                if not url:
                    continue

                if not self.is_useful_result(
                    title,
                    url,
                ):
                    continue

                product = self.extract_product_page(
                    url,
                    fallback_name=title,
                )

                if product:

                    results.append(
                        product
                    )

            except Exception as e:

                print(
                    "Result parsing error:",
                    e,
                )

        return results

    def extract_product_page(
        self,
        url: str,
        fallback_name: str | None = None,
    ) -> Product | None:

        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/125.0 Safari/537.36"
            ),
            "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
        }

        try:

            response = requests.get(
                url,
                headers=headers,
                timeout=15,
                allow_redirects=True,
            )

            response.raise_for_status()

        except Exception as e:

            print(
                "Page fetch error:",
                url,
                e,
            )

            return None

        soup = BeautifulSoup(
            response.text,
            "html.parser",
        )

        name = self.extract_name(
            soup,
            fallback_name,
        )

        if not name:
            return None

        price, currency = self.extract_price(
            soup
        )

        if not self.is_reasonable_price(
            name,
            price,
        ):

            price = None
            currency = None

        rating = self.extract_rating(
            soup
        )

        reviews = self.extract_reviews(
            soup
        )

        seller = self.extract_seller(
            soup
        )

        shop = self.detect_shop(
            url
        )

        return Product(
            name=name,
            shop=shop,
            url=url,
            price=price,
            currency=currency,
            rating=rating,
            reviews=reviews,
            seller=seller,
            is_exact_match=False,
        )

    def extract_name(
        self,
        soup,
        fallback_name=None,
    ):

        # JSON-LD
        for script in soup.find_all(
            "script",
            type="application/ld+json",
        ):

            try:

                data = json.loads(
                    script.string or script.get_text()
                )

                objects = []

                if isinstance(data, list):
                    objects.extend(data)

                elif isinstance(data, dict):

                    if "@graph" in data:
                        objects.extend(
                            data["@graph"]
                        )

                    else:
                        objects.append(data)

                for item in objects:

                    if not isinstance(
                        item,
                        dict,
                    ):
                        continue

                    item_type = item.get(
                        "@type"
                    )

                    if (
                        item_type == "Product"
                        or (
                            isinstance(
                                item_type,
                                list,
                            )
                            and "Product"
                            in item_type
                        )
                    ):

                        name = item.get(
                            "name"
                        )

                        if name:
                            return str(
                                name
                            ).strip()

            except Exception:
                pass

        # OpenGraph
        meta = soup.find(
            "meta",
            property="og:title",
        )

        if meta and meta.get("content"):

            return meta.get(
                "content"
            ).strip()

        # HTML title
        if soup.title:

            title = soup.title.get_text(
                " ",
                strip=True,
            )

            if title:
                return title

        return fallback_name

    def extract_price(
        self,
        soup,
    ):

        # 1. JSON-LD
        result = self.extract_jsonld_price(
            soup
        )

        if result:
            return result

        # 2. Meta tags
        meta_price_names = [
            "product:price:amount",
            "og:price:amount",
            "price",
        ]

        for name in meta_price_names:

            meta = soup.find(
                "meta",
                attrs={
                    "property": name
                },
            )

            if not meta:

                meta = soup.find(
                    "meta",
                    attrs={
                        "name": name
                    },
                )

            if meta and meta.get(
                "content"
            ):

                price = self.parse_number(
                    meta.get(
                        "content"
                    )
                )

                if price is not None:

                    currency = self.detect_currency(
                        meta.get(
                            "content"
                        )
                    )

                    if not currency:

                        currency = self.detect_currency(
                            str(soup)
                        )

                    return (
                        price,
                        currency,
                    )

        # 3. HTML price elements
        selectors = [
            "[itemprop='price']",
            "[data-price]",
            ".price",
            ".product-price",
            ".current-price",
            ".sale-price",
        ]

        for selector in selectors:

            elements = soup.select(
                selector
            )

            for element in elements[:10]:

                value = (
                    element.get(
                        "content"
                    )
                    or element.get(
                        "data-price"
                    )
                    or element.get_text(
                        " ",
                        strip=True,
                    )
                )

                price = self.parse_number(
                    value
                )

                if price is not None:

                    currency = (
                        element.get(
                            "currency"
                        )
                        or self.detect_currency(
                            value
                        )
                        or self.detect_currency(
                            str(soup)
                        )
                    )

                    return (
                        price,
                        currency,
                    )

        # 4. Text fallback
        text = soup.get_text(
            " ",
            strip=True,
        )

        patterns = [

            r"(\d[\d\s.,]{1,12})\s*(₽|руб(?:\.|лей|ля)?)",

            r"(\d[\d\s.,]{1,12})\s*(\$|USD)",

            r"(\d[\d\s.,]{1,12})\s*(€|EUR|евро)",

            r"(\d[\d\s.,]{1,12})\s*(BYN|р\b)",

            r"(\d[\d\s.,]{1,12})\s*(PLN|злотых|злот)",
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                text,
                flags=re.IGNORECASE,
            )

            if not match:
                continue

            price = self.parse_number(
                match.group(1)
            )

            if price is None:
                continue

            currency = self.detect_currency(
                match.group(2)
            )

            return (
                price,
                currency,
            )

        return None, None

    def extract_jsonld_price(
        self,
        soup,
    ):

        for script in soup.find_all(
            "script",
            type="application/ld+json",
        ):

            try:

                data = json.loads(
                    script.string or script.get_text()
                )

                objects = []

                if isinstance(data, list):
                    objects.extend(data)

                elif isinstance(data, dict):

                    if "@graph" in data:
                        objects.extend(
                            data["@graph"]
                        )

                    else:
                        objects.append(data)

                for item in objects:

                    if not isinstance(
                        item,
                        dict,
                    ):
                        continue

                    offers = item.get(
                        "offers"
                    )

                    if not offers:
                        continue

                    if isinstance(
                        offers,
                        list,
                    ):
                        offers = offers[0]

                    if not isinstance(
                        offers,
                        dict,
                    ):
                        continue

                    price = offers.get(
                        "price"
                    )

                    if price is None:

                        price = offers.get(
                            "lowPrice"
                        )

                    if price is None:
                        continue

                    value = self.parse_number(
                        str(price)
                    )

                    if value is None:
                        continue

                    currency = (
                        offers.get(
                            "priceCurrency"
                        )
                        or self.detect_currency(
                            str(offers)
                        )
                    )

                    return (
                        value,
                        self.detect_currency(
                            currency
                        ),
                    )

            except Exception:
                continue

        return None

    def extract_rating(
        self,
        soup,
    ):

        selectors = [
            "[itemprop='ratingValue']",
            "[data-rating]",
        ]

        for selector in selectors:

            element = soup.select_one(
                selector
            )

            if not element:
                continue

            value = (
                element.get(
                    "content"
                )
                or element.get(
                    "data-rating"
                )
                or element.get_text(
                    " ",
                    strip=True,
                )
            )

            match = re.search(
                r"\d+(?:[.,]\d+)?",
                value,
            )

            if match:

                try:

                    rating = float(
                        match.group(0)
                        .replace(",", ".")
                    )

                    if 0 < rating <= 5:
                        return rating

                except Exception:
                    pass

        return None

    def extract_reviews(
        self,
        soup,
    ):

        selectors = [
            "[itemprop='reviewCount']",
            "[itemprop='ratingCount']",
        ]

        for selector in selectors:

            element = soup.select_one(
                selector
            )

            if not element:
                continue

            value = (
                element.get(
                    "content"
                )
                or element.get_text(
                    " ",
                    strip=True,
                )
            )

            match = re.search(
                r"\d[\d\s.,]*",
                value,
            )

            if match:

                try:

                    return int(
                        re.sub(
                            r"\D",
                            "",
                            match.group(0),
                        )
                    )

                except Exception:
                    pass

        return None

    def extract_seller(
        self,
        soup,
    ):

        selectors = [
            "[itemprop='seller']",
            "[itemprop='brand']",
        ]

        for selector in selectors:

            element = soup.select_one(
                selector
            )

            if element:

                value = (
                    element.get(
                        "content"
                    )
                    or element.get_text(
                        " ",
                        strip=True,
                    )
                )

                if value:
                    return value[:150]

        return None

    def parse_number(
        self,
        value,
    ):

        if not value:
            return None

        text = str(value)

        text = (
            text
            .replace("\xa0", " ")
            .strip()
        )

        # Убираем всё кроме цифр,
        # пробелов, точек и запятых.
        text = re.sub(
            r"[^\d\s.,]",
            "",
            text,
        )

        if not text:
            return None

        text = text.replace(
            " ",
            "",
        )

        # 49 999 → 49999
        # 49.999 в ценах часто означает 49999
        # если точка разделяет тысячи.
        if (
            "." in text
            and "," not in text
        ):

            parts = text.split(".")

            if (
                len(parts) > 1
                and all(
                    len(part) == 3
                    for part in parts[1:]
                )
            ):

                text = "".join(parts)

        # 49,999 → 49999
        elif (
            "," in text
            and "." not in text
        ):

            parts = text.split(",")

            if (
                len(parts) > 1
                and all(
                    len(part) == 3
                    for part in parts[1:]
                )
            ):

                text = "".join(parts)

            else:

                text = text.replace(
                    ",",
                    ".",
                )

        # 49.999,50 → 49999.50
        elif (
            "." in text
            and "," in text
        ):

            if text.rfind(",") > text.rfind("."):

                text = (
                    text
                    .replace(".", "")
                    .replace(",", ".")
                )

            else:

                text = text.replace(
                    ",",
                    "",
                )

        try:

            return float(text)

        except ValueError:

            return None

    def detect_currency(
        self,
        text,
    ):

        if not text:
            return None

        value = str(text).lower()

        if (
            "$" in value
            or "usd" in value
            or "доллар" in value
        ):
            return "USD"

        if (
            "€" in value
            or "eur" in value
            or "евро" in value
        ):
            return "EUR"

        if (
            "₽" in value
            or "руб" in value
            or "rub" in value
        ):
            return "RUB"

        if (
            "byn" in value
            or re.search(
                r"\bр\b",
                value,
            )
        ):
            return "BYN"

        if (
            "pln" in value
            or "злот" in value
        ):
            return "PLN"

        if (
            "₸" in value
            or "kzt" in value
            or "тенге" in value
        ):
            return "KZT"

        if (
            "₴" in value
            or "uah" in value
            or "грив" in value
        ):
            return "UAH"

        if (
            "cny" in value
            or "юан" in value
        ):
            return "CNY"

        return None

    def detect_shop(
        self,
        url,
    ):

        hostname = (
            urlparse(url)
            .netloc
            .lower()
            .replace(
                "www.",
                "",
            )
        )

        domains = {
            "ozon.ru": "ozon",
            "ozon.by": "ozon",
            "wildberries.ru": "wildberries",
            "dns-shop.ru": "dns",
            "shop.megafon.ru": "megafon",
            "mts.ru": "mts",
            "aliexpress.com": "aliexpress",
            "amazon.com": "amazon",
            "amazon.de": "amazon",
            "amazon.fr": "amazon",
            "ebay.com": "ebay",
            "ebay.de": "ebay",
            "temu.com": "temu",
            "walmart.com": "walmart",
        }

        for domain, shop in domains.items():

            if (
                hostname == domain
                or hostname.endswith(
                    "." + domain
                )
            ):
                return shop

        return "web"

    def is_useful_result(
        self,
        title,
        url,
    ):

        text = (
            title + " " + url
        ).lower()

        bad_words = [
            "новости",
            "новость",
            "статья",
            "обзор",
            "сравнение",
            "википедия",
            "wiki",
            "категория",
            "/catalog/",
            "/category/",
        ]

        if any(
            word in text
            for word in bad_words
        ):
            return False

        return True

    def is_reasonable_price(
        self,
        name,
        price,
    ):

        if price is None:
            return True

        if price <= 0:
            return False

        text = name.lower()

        expensive_keywords = [
            "iphone",
            "айфон",
            "apple",
            "samsung",
            "galaxy",
            "pixel",
            "macbook",
            "playstation",
            "xbox",
            "sony",
            "смартфон",
            "телефон",
            "ноутбук",
            "телевизор",
            "tv",
        ]

        if (
            price < 10
            and any(
                word in text
                for word in expensive_keywords
            )
        ):
            return False

        if price > 50000000:
            return False

        return True