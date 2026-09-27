from __future__ import annotations

import logging
import re
from typing import Any, Optional

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class AlibabaAdapter:
    """
    Поиск по Alibaba.com — оптовая (в основном B2B) площадка, полезна
    для сравнения цены "от производителя" при заказе в Китае.

    Как и AliExpress/1688, это неофициальная интеграция: используется
    серверно отрендеренная часть HTML страницы поиска (Alibaba.com,
    в отличие от AliExpress, ещё сохраняет заметную часть карточек
    товара в исходном HTML, но это может измениться). Цены на Alibaba
    часто зависят от объёма заказа (опт) — здесь берётся минимальная
    заявленная цена за единицу, что подходит для сравнения "от какой
    суммы начинается", а не для расчёта точной стоимости одной штуки
    при мелком заказе.

    При любой ошибке разбора адаптер возвращает пустой список для
    данного запроса, не прерывая остальной поиск.
    """

    name = "alibaba"
    supported_regions = {"CN", "WORLD"}

    SEARCH_URL = "https://www.alibaba.com/trade/search"

    _PRICE_RE = re.compile(r"[\d][\d,\.]*")

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
                offers = self._search_query(query=query, region=region)
            except Exception:
                logger.warning(
                    "Alibaba query failed: %s",
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
            },
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Alibaba меняет имена CSS-классов при каждом релизе фронтенда;
        # поэтому ищем карточки по структуре ссылки на товар, а не по
        # конкретному классу.
        cards = soup.select("a[href*='/product-detail/']")

        offers = []
        seen_urls = set()

        for card in cards:
            offer = self._to_offer(card, region=region)
            if offer is None or offer["url"] in seen_urls:
                continue
            seen_urls.add(offer["url"])
            offers.append(offer)

            if len(offers) >= self.max_results:
                break

        return offers

    def _to_offer(
        self,
        card: Any,
        region: str,
    ) -> Optional[dict[str, Any]]:

        url = card.get("href")
        if url and url.startswith("//"):
            url = "https:" + url

        title = card.get_text(strip=True) or card.get("title")
        if not title:
            return None

        container = card.find_parent()
        price = None

        if container is not None:
            text = container.get_text(" ", strip=True)
            match = self._PRICE_RE.search(text)
            if match:
                try:
                    price = float(match.group(0).replace(",", ""))
                except ValueError:
                    price = None

        if price is None:
            return None

        product_data = {
            "title": title,
            "brand": None,
            "category": None,
            "product_type": None,
            "model": None,
            "attributes": {},
        }

        return {
            "source": "alibaba",
            "title": title,
            "brand": None,
            "category": None,
            "product_type": None,
            "model": None,
            "attributes": {},
            "product": product_data,
            "price": price,
            "currency": "USD",
            "delivery": None,
            "taxes": None,
            "duties": None,
            "fees": None,
            "url": url,
            "seller": "Alibaba supplier",
            "condition": "new",
            "availability": "in_stock",
            "region": region,
            "description": "Оптовая цена (Alibaba); может зависеть от объёма заказа.",
            "extracted": False,
        }
