import re
from html import unescape
from urllib.parse import unquote

import requests

from products import Product
from adapters.base import ShopAdapter


class WebSearchAdapter(ShopAdapter):

    @property
    def shop_name(self) -> str:
        return "web_search"

    def can_handle(self, url: str) -> bool:
        return False

    def get_product(self, url: str) -> Product | None:
        return None

    def search(self, query: str) -> list[Product]:

        try:

            search_url = "https://html.duckduckgo.com/html/"

            headers = {
                "User-Agent": (
                    "Mozilla/5.0 "
                    "(iPhone; CPU iPhone OS 18_7 like Mac OS X) "
                    "AppleWebKit/605.1.15 "
                    "(KHTML, like Gecko) "
                    "Version/18.0 Mobile/15E148 Safari/604.1"
                ),
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
            }

            response = requests.get(
                search_url,
                params={
                    "q": query,
                    "kl": "ru-ru",
                },
                headers=headers,
                timeout=15,
            )

            response.raise_for_status()

            html = response.text

            results = []

            pattern = (
                r'class="result__a"[^>]*href="([^"]+)"'
                r'[^>]*>(.*?)</a>'
            )

            matches = re.findall(
                pattern,
                html,
                re.IGNORECASE | re.DOTALL,
            )

            for link, title in matches[:30]:

                title = re.sub(
                    r"<.*?>",
                    "",
                    title,
                )

                title = unescape(
                    title
                ).strip()

                link = unquote(
                    link
                ).strip()

                if not title or not link:
                    continue

                if "uddg=" in link:

                    match = re.search(
                        r"uddg=([^&]+)",
                        link,
                    )

                    if match:
                        link = unquote(
                            match.group(1)
                        )

                if not self.is_product_result(
                    title,
                    link,
                ):
                    continue

                shop = self.detect_shop(
                    link
                )

                price, currency = self.extract_price(
                    title
                )

                if price is None:

                    page_price, page_currency = (
                        self.get_page_price(
                            link,
                            query,
                        )
                    )

                    if page_price is not None:

                        price = page_price
                        currency = page_currency

                # Дополнительная проверка цены.
                if not self.is_reasonable_price(
                    price,
                    title,
                    query,
                ):
                    price = None
                    currency = None

                results.append(
                    Product(
                        name=title,
                        shop=shop,
                        url=link,
                        price=price,
                        currency=currency,
                        is_exact_match=False,
                    )
                )

                if len(results) >= 10:
                    break

            print(
                f"Web search: found {len(results)} "
                f"results for '{query}'"
            )

            return results

        except Exception as e:

            print(
                "Web search error:",
                e,
            )

            return []

    def get_page_price(
        self,
        url: str,
        query: str,
    ):

        try:

            headers = {
                "User-Agent": (
                    "Mozilla/5.0 "
                    "(iPhone; CPU iPhone OS 18_7 like Mac OS X) "
                    "AppleWebKit/605.1.15 "
                    "(KHTML, like Gecko) "
                    "Version/18.0 Mobile/15E148 Safari/604.1"
                ),
                "Accept": "text/html,application/xhtml+xml",
                "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
            }

            response = requests.get(
                url,
                headers=headers,
                timeout=10,
                allow_redirects=True,
            )

            if response.status_code != 200:
                return None, None

            html = response.text

            # JSON-LD
            price = self.extract_json_price(
                html
            )

            if price:
                if self.is_reasonable_price(
                    price[0],
                    "",
                    query,
                ):
                    return price

            # HTML metadata
            price = self.extract_html_price(
                html
            )

            if price:
                if self.is_reasonable_price(
                    price[0],
                    "",
                    query,
                ):
                    return price

            # Обычный текст страницы.
            text = re.sub(
                r"<script.*?</script>",
                " ",
                html,
                flags=re.IGNORECASE | re.DOTALL,
            )

            text = re.sub(
                r"<style.*?</style>",
                " ",
                text,
                flags=re.IGNORECASE | re.DOTALL,
            )

            text = re.sub(
                r"<.*?>",
                " ",
                text,
            )

            text = unescape(
                text
            )

            price = self.extract_price(
                text
            )

            if price:

                if self.is_reasonable_price(
                    price[0],
                    "",
                    query,
                ):
                    return price

        except Exception as e:

            print(
                "Page price error:",
                e,
            )

        return None, None

    def extract_json_price(
        self,
        html: str,
    ):

        patterns = [

            r'"price"\s*:\s*"([\d\s.,]+)"',

            r'"price"\s*:\s*([\d.]+)',

            r'"lowPrice"\s*:\s*"([\d\s.,]+)"',

            r'"lowPrice"\s*:\s*([\d.]+)',
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                html,
                re.IGNORECASE,
            )

            if not match:
                continue

            try:

                value = (
                    match.group(1)
                    .replace(" ", "")
                    .replace(",", ".")
                )

                price = float(value)

                if 0 < price < 100000000:

                    currency = self.detect_currency(
                        html
                    )

                    return price, currency

            except Exception:
                continue

        return None

    def extract_html_price(
        self,
        html: str,
    ):

        patterns = [

            r'itemprop=["\']price["\'][^>]*content=["\']([\d.,]+)',

            r'content=["\']([\d.,]+)["\'][^>]*itemprop=["\']price',

            r'meta[^>]+property=["\']product:price:amount["\'][^>]+content=["\']([\d.,]+)',
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                html,
                re.IGNORECASE,
            )

            if not match:
                continue

            try:

                value = (
                    match.group(1)
                    .replace(",", ".")
                )

                price = float(value)

                if 0 < price < 100000000:

                    currency = self.detect_currency(
                        html
                    )

                    return price, currency

            except Exception:
                continue

        return None

    def extract_price(
        self,
        text: str,
    ):

        patterns = [

            r"(\d[\d\s.,]*)\s*(₽|руб\.?|RUB)",

            r"(\$)\s*(\d[\d\s.,]*)",

            r"(\d[\d\s.,]*)\s*(\$|USD)",

            r"(\d[\d\s.,]*)\s*(€|EUR)",

            r"(\d[\d\s.,]*)\s*(BYN|Br)",

            r"(\d[\d\s.,]*)\s*(грн|UAH)",

            r"(\d[\d\s.,]*)\s*(₸|KZT)",
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                text,
                re.IGNORECASE,
            )

            if not match:
                continue

            try:

                numbers = [
                    item
                    for item in match.groups()
                    if re.search(
                        r"\d",
                        item,
                    )
                ]

                if not numbers:
                    continue

                number = numbers[0]

                number = (
                    number
                    .replace(" ", "")
                    .replace(",", ".")
                )

                price = float(number)

                currency = self.detect_currency(
                    text
                )

                if 0 < price < 100000000:

                    return price, currency

            except Exception:
                continue

        return None, None

    def is_reasonable_price(
        self,
        price,
        title: str,
        query: str,
    ) -> bool:

        if price is None:
            return False

        if price <= 0:
            return False

        text = (
            title + " " + query
        ).lower()

        # Защита от случайных маленьких чисел.
        if price < 10:

            expensive_keywords = [
                "iphone",
                "apple",
                "samsung",
                "sony",
                "macbook",
                "playstation",
                "телефон",
                "смартфон",
                "ноутбук",
                "телевизор",
                "куртка",
                "обувь",
            ]

            for word in expensive_keywords:

                if word in text:
                    return False

        # Защита от явно подозрительных
        # экстремально больших значений.
        if price > 50000000:
            return False

        return True

    def is_product_result(
        self,
        title: str,
        url: str,
    ) -> bool:

        text = (
            title + " " + url
        ).lower()

        blocked_words = [
            "/category/",
            "/categories/",
            "/blog/",
            "/article/",
            "/news/",
            "/search?",
            "каталог",
            "категория",
            "лучшие ",
            "топ ",
            "обзор",
            "рейтинг",
            "как выбрать",
        ]

        for word in blocked_words:

            if word in text:
                return False

        product_words = [
            "купить",
            "цена",
            "руб",
            "₽",
            "byn",
            "br",
            "usd",
            "$",
            "eur",
            "€",
            "товар",
            "product",
            "iphone",
            "samsung",
            "sony",
            "apple",
            "xiaomi",
            "куртка",
            "кроссовки",
            "телефон",
            "наушники",
        ]

        for word in product_words:

            if word in text:
                return True

        shop_domains = [
            "wildberries.",
            "ozon.",
            "amazon.",
            "ebay.",
            "aliexpress.",
            "temu.",
            "walmart.",
            "etsy.",
            "rozetka.",
            "kaspi.",
        ]

        for domain in shop_domains:

            if domain in url.lower():
                return True

        return False

    def detect_currency(
        self,
        text: str,
    ) -> str | None:

        text = text.lower()

        if "₽" in text or "руб" in text:
            return "RUB"

        if "$" in text or "usd" in text:
            return "USD"

        if "€" in text or "eur" in text:
            return "EUR"

        if "byn" in text or " br" in text:
            return "BYN"

        if "₴" in text or "грн" in text:
            return "UAH"

        if "₸" in text or "kzt" in text:
            return "KZT"

        return None

    def detect_shop(
        self,
        url: str,
    ) -> str:

        url_lower = url.lower()

        shops = {
            "wildberries.ru": "wildberries",
            "wildberries.by": "wildberries",
            "ozon.ru": "ozon",
            "ozon.by": "ozon",
            "amazon.": "amazon",
            "ebay.": "ebay",
            "walmart.com": "walmart",
            "aliexpress.": "aliexpress",
            "temu.com": "temu",
            "etsy.com": "etsy",
            "shein.com": "shein",
            "taobao.com": "taobao",
            "1688.com": "1688",
            "jd.com": "jd",
            "kaspi.kz": "kaspi",
            "rozetka.": "rozetka",
            "market.yandex.": "yandex_market",
        }

        for domain, shop in shops.items():

            if domain in url_lower:
                return shop

        return "web"