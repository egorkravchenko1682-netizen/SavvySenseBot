from __future__ import annotations

import json
import logging
import re
from typing import Any, Optional

import requests

logger = logging.getLogger(__name__)


class AliExpressAdapter:
    """
    Поиск по AliExpress — источник товаров напрямую из Китая с
    доставкой практически в любую страну.

    ЧЕСТНО О ГРАНИЦАХ ЭТОГО АДАПТЕРА:
    AliExpress — это, по сути, JavaScript-приложение: большая часть
    страницы поиска рендерится в браузере, а не приходит готовым HTML
    от сервера. Простой HTTP-запрос (`requests`, без браузера) часто
    видит только "пустой каркас" страницы.

    Что делает этот адаптер: многие страницы AliExpress всё же
    вставляют начальный набор товаров как JSON прямо в HTML (в блоке
    `window.runParams = {...}`), чтобы ускорить первую отрисовку —
    это распространённый и хорошо задокументированный в открытых
    scraper-проектах приём. Адаптер ищет этот блок и парсит его.

    Если AliExpress перестанет вставлять этот блок (изменит фронтенд)
    или отдаст капчу — регулярный риск для любого неофициального
    скрейпинга — адаптер вернёт пустой список, как и любой другой
    отказавший источник в этом проекте. Официальный путь для
    надёжной интеграции — AliExpress Open Platform / Affiliate API,
    который требует регистрации партнёра и одобрения; при наличии
    такого доступа этот файл — единственное место, которое нужно
    переписать.
    """

    name = "aliexpress"
    supported_regions = {"CN", "WORLD"}

    SEARCH_URL = "https://www.aliexpress.com/wholesale"

    _RUN_PARAMS_RE = re.compile(
        r"window\.runParams\s*=\s*(\{.*?\});",
        re.DOTALL,
    )

    def __init__(
        self,
        max_results: int = 10,
        timeout: int = 12,
    ) -> None:
        self.max_results = max_results
        self.timeout = timeout

    def search(
        self,
        queries: list[str],
        region: str,
        currency: str,
        budget: Optional[dict[str, Any]] = None,
    ) -> list[dict[str, Any]]:

        all_offers: list[dict[str, Any]] = []

        for query in queries:
            try:
                offers = self._search_query(
                    query=query,
                    region=region,
                    currency=currency,
                )
            except Exception:
                logger.warning(
                    "AliExpress query failed: %s",
                    query,
                    exc_info=True,
                )
                continue

            all_offers.extend(offers)

            if len(all_offers) >= self.max_results:
                break

        return all_offers[: self.max_results]

    def _search_query(
        self,
        query: str,
        region: str,
        currency: str,
    ) -> list[dict[str, Any]]:

        response = requests.get(
            self.SEARCH_URL,
            params={"SearchText": query},
            timeout=self.timeout,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0 Safari/537.36"
                ),
                "Accept-Language": "en-US,en;q=0.9",
            },
        )
        response.raise_for_status()

        items = self._extract_items(response.text)

        offers = []
        for item in items[: self.max_results]:
            offer = self._to_offer(item, region=region, currency=currency)
            if offer is not None:
                offers.append(offer)

        return offers

    @classmethod
    def _extract_items(cls, html: str) -> list[dict[str, Any]]:
        match = cls._RUN_PARAMS_RE.search(html)
        if not match:
            return []

        try:
            run_params = json.loads(match.group(1))
        except (TypeError, ValueError):
            return []

        # Точный путь до списка товаров менялся у AliExpress не раз;
        # проверяем несколько известных вариантов вместо одного
        # жёстко зашитого пути.
        candidates = [
            (
                run_params.get("data", {})
                .get("root", {})
                .get("fields", {})
                .get("mods", {})
                .get("itemList", {})
                .get("content")
            ),
            run_params.get("mods", {}).get("itemList", {}).get("content"),
        ]

        for candidate in candidates:
            if candidate:
                return candidate

        return []

    @staticmethod
    def _to_offer(
        item: dict[str, Any],
        region: str,
        currency: str,
    ) -> Optional[dict[str, Any]]:

        price_info = item.get("prices", {}).get("salePrice") or item.get(
            "prices", {}
        ).get("originalPrice") or {}

        price = price_info.get("minPrice")

        if price is None:
            return None

        try:
            price = float(price)
        except (TypeError, ValueError):
            return None

        item_currency = price_info.get("currencyCode") or "USD"
        title = item.get("title", {}).get("displayTitle") or item.get("title")
        product_id = item.get("productId")

        url = None
        if product_id:
            url = f"https://www.aliexpress.com/item/{product_id}.html"

        product_data = {
            "title": title,
            "brand": None,
            "category": None,
            "product_type": None,
            "model": None,
            "attributes": {},
        }

        return {
            "source": "aliexpress",
            "title": title,
            "brand": None,
            "category": None,
            "product_type": None,
            "model": None,
            "attributes": {},
            "product": product_data,
            "price": price,
            "currency": item_currency,
            "delivery": None,
            "taxes": None,
            "duties": None,
            "fees": None,
            "url": url,
            "seller": item.get("store", {}).get("storeName") or "AliExpress seller",
            "condition": "new",
            "availability": "in_stock",
            "region": region,
            "description": None,
            "extracted": False,
            "rating": item.get("evaluation", {}).get("starRating"),
        }
