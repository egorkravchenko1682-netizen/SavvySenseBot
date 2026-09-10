import re
import requests

from products import Product
from adapters.base import ShopAdapter


class WildberriesAdapter(ShopAdapter):

    @property
    def shop_name(self) -> str:
        return "wildberries"

    def can_handle(self, url: str) -> bool:
        return "wildberries.ru" in url.lower()

    def extract_product_id(self, url: str) -> str | None:
        patterns = [
            r"/catalog/(\d+)/detail",
            r"/catalog/(\d+)",
        ]

        for pattern in patterns:
            match = re.search(pattern, url)

            if match:
                return match.group(1)

        return None

    def get_product(self, url: str) -> Product | None:
        product_id = self.extract_product_id(url)

        if not product_id:
            return None

        api_url = "https://card.wb.ru/cards/v4/detail"

        params = {
            "appType": 1,
            "curr": "rub",
            "dest": -1257786,
            "lang": "ru",
            "nm": product_id,
        }

        headers = {
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
        }

        try:
            response = requests.get(
                api_url,
                params=params,
                headers=headers,
                timeout=10,
            )

            response.raise_for_status()

            data = response.json()

            products = data.get("products", [])

            if not products:
                products = data.get(
                    "data", {}
                ).get("products", [])

            if not products:
                return None

            item = products[0]

            price = None

            sizes = item.get("sizes", [])

            if sizes:
                price_data = sizes[0].get("price", {})

                if "product" in price_data:
                    price = price_data["product"] / 100

            return Product(
                name=item.get("name", "Без названия"),
                shop="wildberries",
                url=url,
                price=price,
                currency="RUB",
                brand=item.get("brand"),
                rating=item.get("reviewRating"),
                reviews=item.get("feedbacks"),
                product_id=product_id,
                is_exact_match=True,
            )

        except Exception as e:
            print("Wildberries error:", e)
            return None

    def search(self, query: str) -> list[Product]:
        # Глобальный поиск будет подключён
        # через отдельный поисковый слой.
        return []