import base64
import time
import requests

from products import Product
from adapters.base import ShopAdapter


class EbayApiAdapter(ShopAdapter):

    TOKEN_URL = "https://api.ebay.com/identity/v1/oauth2/token"
    SEARCH_URL = "https://api.ebay.com/buy/browse/v1/item_summary/search"

    def __init__(self):
        self.client_id = None
        self.client_secret = None
        self.access_token = None
        self.token_expires_at = 0

        import os

        self.client_id = os.getenv("EBAY_CLIENT_ID")
        self.client_secret = os.getenv("EBAY_CLIENT_SECRET")

    @property
    def shop_name(self) -> str:
        return "ebay"

    def can_handle(self, url: str) -> bool:
        if not url:
            return False

        url = url.lower()

        return any(
            domain in url
            for domain in [
                "ebay.com",
                "ebay.de",
                "ebay.fr",
                "ebay.co.uk",
                "ebay.pl",
            ]
        )

    def get_access_token(self):
        if (
            self.access_token
            and time.time() < self.token_expires_at - 60
        ):
            return self.access_token

        if not self.client_id or not self.client_secret:
            print("eBay credentials are missing")
            return None

        credentials = f"{self.client_id}:{self.client_secret}"

        encoded_credentials = base64.b64encode(
            credentials.encode("utf-8")
        ).decode("utf-8")

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Authorization": f"Basic {encoded_credentials}",
        }

        data = {
            "grant_type": "client_credentials",
            "scope": "https://api.ebay.com/oauth/api_scope",
        }

        try:
            response = requests.post(
                self.TOKEN_URL,
                headers=headers,
                data=data,
                timeout=15,
            )

            response.raise_for_status()

            result = response.json()

            self.access_token = result.get("access_token")

            expires_in = int(
                result.get("expires_in", 7200)
            )

            self.token_expires_at = (
                time.time() + expires_in
            )

            print("eBay OAuth token received")

            return self.access_token

        except Exception as e:
            print("eBay OAuth error:", e)
            return None

    def search(self, query: str) -> list[Product]:

        token = self.get_access_token()

        if not token:
            return []

        headers = {
            "Authorization": f"Bearer {token}",
            "X-EBAY-C-MARKETPLACE-ID": "EBAY_US",
            "Accept": "application/json",
        }

        params = {
            "q": query,
            "limit": 10,
        }

        try:
            response = requests.get(
                self.SEARCH_URL,
                headers=headers,
                params=params,
                timeout=20,
            )

            response.raise_for_status()

            data = response.json()

            items = data.get("itemSummaries", [])

            results = []

            for item in items:

                title = item.get(
                    "title",
                    "Без названия",
                )

                item_url = item.get(
                    "itemWebUrl"
                )

                price = None
                currency = None

                price_data = item.get(
                    "price"
                )

                if price_data:
                    try:
                        price = float(
                            price_data.get(
                                "value"
                            )
                        )
                    except (
                        TypeError,
                        ValueError,
                    ):
                        price = None

                    currency = (
                        price_data.get(
                            "currency"
                        )
                    )

                image_url = None

                image_data = item.get(
                    "image"
                )

                if image_data:
                    image_url = image_data.get(
                        "imageUrl"
                    )

                seller = None

                seller_data = item.get(
                    "seller"
                )

                if seller_data:
                    seller = seller_data.get(
                        "username"
                    )

                rating = None

                if seller_data:
                    try:
                        rating = float(
                            seller_data.get(
                                "feedbackPercentage"
                            )
                        )
                    except (
                        TypeError,
                        ValueError,
                    ):
                        rating = None

                results.append(
                    Product(
                        name=title,
                        shop="ebay",
                        url=item_url or "",
                        price=price,
                        currency=currency,
                        image_url=image_url,
                        seller=seller,
                        rating=rating,
                        product_id=item.get(
                            "itemId"
                        ),
                    )
                )

            print(
                "eBay results:",
                len(results),
            )

            return results

        except Exception as e:
            print(
                "eBay search error:",
                e,
            )
            return []

    def get_product(self, url: str) -> Product | None:
        return None