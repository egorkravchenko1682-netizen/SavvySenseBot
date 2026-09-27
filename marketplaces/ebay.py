from __future__ import annotations

import logging
import os
import time
from typing import Any, Optional

import requests

logger = logging.getLogger(__name__)


class EbayAdapter:
    """
    Поиск по eBay через официальный Browse API.

    В отличие от Wildberries/Ozon/AliExpress/1688 в этом файле — это
    задокументированный, официальный API eBay, а не разбор внутренней
    вёрстки сайта. Для работы нужны учётные данные приложения eBay
    (бесплатная регистрация разработчика: https://developer.ebay.com):

        EBAY_CLIENT_ID=...
        EBAY_CLIENT_SECRET=...

    Без них адаптер не падает — он просто логирует предупреждение один
    раз и возвращает пустой список для каждого запроса (тот же принцип
    "источник недоступен — не мешает остальным", что и у прочих
    адаптеров).
    """

    name = "ebay"
    supported_regions = {"WORLD"}

    TOKEN_URL = "https://api.ebay.com/identity/v1/oauth2/token"
    SEARCH_URL = "https://api.ebay.com/buy/browse/v1/item_summary/search"
    OAUTH_SCOPE = "https://api.ebay.com/oauth/api_scope"

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        marketplace_id: str = "EBAY_US",
        max_results: int = 10,
        timeout: int = 10,
    ) -> None:
        self.client_id = client_id or os.getenv("EBAY_CLIENT_ID")
        self.client_secret = client_secret or os.getenv("EBAY_CLIENT_SECRET")
        self.marketplace_id = marketplace_id
        self.max_results = max_results
        self.timeout = timeout

        self._token: Optional[str] = None
        self._token_expires_at: float = 0.0

    def search(
        self,
        queries: list[str],
        region: str,
        currency: str,
        budget: Optional[dict[str, Any]] = None,
    ) -> list[dict[str, Any]]:

        if not self.client_id or not self.client_secret:
            logger.info(
                "eBay adapter skipped: EBAY_CLIENT_ID/EBAY_CLIENT_SECRET "
                "not configured",
            )
            return []

        all_offers: list[dict[str, Any]] = []

        for query in queries:
            try:
                offers = self._search_query(query=query, region=region)
            except Exception:
                logger.warning(
                    "eBay query failed: %s",
                    query,
                    exc_info=True,
                )
                continue

            all_offers.extend(offers)

            if len(all_offers) >= self.max_results:
                break

        return all_offers[: self.max_results]

    # =========================
    # OAUTH
    # =========================

    def _get_token(self) -> Optional[str]:
        if self._token and time.time() < self._token_expires_at:
            return self._token

        response = requests.post(
            self.TOKEN_URL,
            auth=(self.client_id, self.client_secret),
            data={
                "grant_type": "client_credentials",
                "scope": self.OAUTH_SCOPE,
            },
            timeout=self.timeout,
        )
        response.raise_for_status()

        payload = response.json()
        token = payload.get("access_token")
        expires_in = payload.get("expires_in", 0)

        if not token:
            return None

        self._token = token
        # Обновляем токен на минуту раньше официального истечения —
        # запас на сетевые задержки.
        self._token_expires_at = time.time() + max(expires_in - 60, 0)

        return token

    # =========================
    # SEARCH
    # =========================

    def _search_query(
        self,
        query: str,
        region: str,
    ) -> list[dict[str, Any]]:

        token = self._get_token()
        if not token:
            return []

        response = requests.get(
            self.SEARCH_URL,
            params={"q": query, "limit": self.max_results},
            headers={
                "Authorization": f"Bearer {token}",
                "X-EBAY-C-MARKETPLACE-ID": self.marketplace_id,
            },
            timeout=self.timeout,
        )
        response.raise_for_status()

        payload = response.json()
        items = payload.get("itemSummaries") or []

        offers = []
        for item in items[: self.max_results]:
            offer = self._to_offer(item, region=region)
            if offer is not None:
                offers.append(offer)

        return offers

    @staticmethod
    def _to_offer(
        item: dict[str, Any],
        region: str,
    ) -> Optional[dict[str, Any]]:

        price_info = item.get("price") or {}
        price = price_info.get("value")

        if price is None:
            return None

        try:
            price = float(price)
        except (TypeError, ValueError):
            return None

        currency = price_info.get("currency") or "USD"
        title = item.get("title")
        condition = (item.get("condition") or "").lower()

        product_data = {
            "title": title,
            "brand": None,
            "category": None,
            "product_type": None,
            "model": None,
            "attributes": {},
        }

        return {
            "source": "ebay",
            "title": title,
            "brand": None,
            "category": None,
            "product_type": None,
            "model": None,
            "attributes": {},
            "product": product_data,
            "price": price,
            "currency": currency,
            "delivery": None,
            "taxes": None,
            "duties": None,
            "fees": None,
            "url": item.get("itemWebUrl"),
            "seller": (item.get("seller") or {}).get("username") or "eBay seller",
            "condition": (
                "used"
                if "used" in condition or "refurb" in condition
                else "new"
            ),
            "availability": "in_stock",
            "region": region,
            "description": item.get("shortDescription"),
            "extracted": False,
        }
