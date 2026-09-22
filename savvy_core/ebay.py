import os
import base64

import aiohttp

from .models import Offer, SearchRequest


class EbayProvider:
    name = "ebay"

    async def get_token(self) -> str:
        client_id = os.getenv("EBAY_CLIENT_ID")
        client_secret = os.getenv("EBAY_CLIENT_SECRET")

        if not client_id or not client_secret:
            raise RuntimeError(
                "EBAY_CLIENT_ID or EBAY_CLIENT_SECRET is not configured"
            )

        credentials = f"{client_id}:{client_secret}".encode()
        encoded = base64.b64encode(credentials).decode()

        headers = {
            "Authorization": f"Basic {encoded}",
            "Content-Type": "application/x-www-form-urlencoded",
        }

        data = {
            "grant_type": "client_credentials",
            "scope": "https://api.ebay.com/oauth/api_scope",
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "https://api.ebay.com/identity/v1/oauth2/token",
                headers=headers,
                data=data,
            ) as response:

                if response.status != 200:
                    text = await response.text()
                    raise RuntimeError(
                        f"eBay token error: {response.status} {text}"
                    )

                result = await response.json()
                return result["access_token"]

    async def search(
        self,
        request: SearchRequest,
    ) -> list[Offer]:

        token = await self.get_token()

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        params = {
            "q": " ".join(request.keywords),
            "limit": 10,
        }

        async with aiohttp.ClientSession() as session:
            async with session.get(
                "https://api.ebay.com/buy/browse/v1/item_summary/search",
                headers=headers,
                params=params,
            ) as response:

                if response.status != 200:
                    text = await response.text()
                    raise RuntimeError(
                        f"eBay search error: {response.status} {text}"
                    )

                data = await response.json()

        offers = []

        for item in data.get("itemSummaries", []):

            price_data = item.get("price", {})

            try:
                price = float(price_data.get("value", 0))
            except (TypeError, ValueError):
                continue

            if price <= 0:
                continue

            currency = price_data.get(
                "currency",
                request.currency or "USD",
            )

            offers.append(
                Offer(
                    title=item.get(
                        "title",
                        "eBay product",
                    ),
                    seller="eBay",
                    source="ebay",
                    url=item.get(
                        "itemWebUrl",
                        "",
                    ),
                    price=price,
                    currency=currency,
                    shipping_cost=0.0,
                    delivery_days=None,
                    seller_rating=None,
                )
            )

        return offers