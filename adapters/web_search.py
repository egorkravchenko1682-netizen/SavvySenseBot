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

                # Раскрываем redirect DuckDuckGo
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

                shop = self.detect_shop(link)

                price, currency = self.extract_price(
                    title
                )

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
                f"product results for '{query}'"
            )

            return results

        except Exception as e:

            print(
                "Web search error:",
                e,
            )

            return []

    def is_product_result(
        self,
        title: str,
        url: str,
    ) -> bool:

        text = (
            title + " " + url
        ).lower()

        # Страницы, которые почти всегда
        # являются категориями или статьями.
        blocked_words = [
            "/category/",
            "/categories/",
            "/blog/",
            "/article/",
            "/news/",
            "/search?",
            "/catalog/",
            "купить на ozon",
            "купить на wildberries",
            "каталог",
            "категория",
            "лучшие ",
            "топ ",
            "обзор",
            "рейтинг",
            "как выбрать",
            "гид по покупке",
        ]

        for word in blocked_words:

            if word in text:
                return False

        # Нужен хотя бы один признак,
        # что страница может быть товарной.
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
            "shop",
            "store",
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

        # Некоторые маркетплейсы используют
        # товарные URL без слов "купить".
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

    def extract_price(
        self,
        text: str,
    ):

        patterns = [

            # 1 299 ₽
            r"(\d[\d\s.,]*)\s*(₽|руб\.?|RUB)",

            # $299
            r"(\$)\s*(\d[\d\s.,]*)",

            # 299 $
            r"(\d[\d\s.,]*)\s*(\$|USD)",

            # 299 €
            r"(\d[\d\s.,]*)\s*(€|EUR)",

            # 299 BYN
            r"(\d[\d\s.,]*)\s*(BYN|Br)",

            # 299 грн
            r"(\d[\d\s.,]*)\s*(грн|UAH)",

            # 299 ₸
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

            groups = match.groups()

            try:

                numbers = [
                    item
                    for item in groups
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

                return price, currency

            except Exception:
                continue

        return None, None

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