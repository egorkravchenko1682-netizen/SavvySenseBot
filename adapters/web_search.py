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
                params={"q": query},
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

            for link, title in matches[:15]:

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

                # DuckDuckGo иногда отдаёт
                # ссылку через redirect URL.
                if "uddg=" in link:
                    match = re.search(
                        r"uddg=([^&]+)",
                        link,
                    )

                    if match:
                        link = unquote(
                            match.group(1)
                        )

                shop = self.detect_shop(
                    link
                )

                results.append(
                    Product(
                        name=title,
                        shop=shop,
                        url=link,
                        is_exact_match=False,
                    )
                )

            print(
                f"Web search: found {len(results)} results "
                f"for '{query}'"
            )

            return results

        except Exception as e:

            print(
                "Web search error:",
                e,
            )

            return []

    def detect_shop(self, url: str) -> str:

        url_lower = url.lower()

        shops = {
            "wildberries.ru": "wildberries",
            "ozon.ru": "ozon",
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