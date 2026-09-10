import re
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
                    "(iPhone; CPU iPhone OS 18_0 like Mac OS X) "
                    "AppleWebKit/605.1.15 "
                    "Version/18.0 Mobile/15E148 Safari/604.1"
                )
            }

            response = requests.get(
                search_url,
                params={
                    "q": query
                },
                headers=headers,
                timeout=15
            )

            response.raise_for_status()

            html = response.text

            results = []

            matches = re.findall(
                r'class="result__a"[^>]*href="([^"]+)"[^>]*>(.*?)</a>',
                html,
                re.S
            )

            for link, title in matches[:10]:

                title = re.sub(
                    r"<.*?>",
                    "",
                    title
                ).strip()

                if not title:
                    continue

                shop = self.detect_shop(link)

                results.append(
                    Product(
                        name=title,
                        shop=shop,
                        url=link,
                        is_exact_match=False
                    )
                )

            return results

        except Exception as e:

            print(
                "Web search error:",
                e
            )

            return []

    def detect_shop(self, url: str) -> str:

        url_lower = url.lower()

        shops = {
            "wildberries": "wildberries",
            "ozon": "ozon",
            "amazon": "amazon",
            "ebay": "ebay",
            "walmart": "walmart",
            "aliexpress": "aliexpress",
            "temu": "temu",
            "etsy": "etsy",
            "shein": "shein",
            "taobao": "taobao",
            "1688": "1688",
            "jd.com": "jd",
            "kaspi": "kaspi",
            "rozetka": "rozetka",
        }

        for domain, shop in shops.items():

            if domain in url_lower:
                return shop

        return "web"