from __future__ import annotations

import logging
import os
import re
from typing import Any, Optional

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class China1688Adapter:
    """
    Поиск по 1688.com — внутренний китайский B2B-рынок (тот же
    holding, что и Alibaba/AliExpress), часто даёт САМУЮ низкую цену
    "от завода", но ориентирован на покупателей внутри Китая.

    ЭТО САМЫЙ НЕНАДЁЖНЫЙ АДАПТЕР В ПРОЕКТЕ — честно предупреждаю:
    - интерфейс 1688.com преимущественно на китайском и рассчитан на
      посредников с китайским номером телефона для полного доступа;
    - сайт активно блокирует запросы не из Китая и без полноценной
      browser-сессии (JS-испытания, капча) — обычный `requests`,
      вероятнее всего, получит страницу-заглушку, а не список товаров;
    - реальная надёжная интеграция обычно требует headless-браузер
      (Playwright/Selenium с китайским прокси) либо платный доступ
      через дата-провайдера — это уже не просто "новый адаптер",
      а отдельная инфраструктурная задача.

    Поэтому адаптер ВЫКЛЮЧЕН по умолчанию. Чтобы попробовать его
    (например, запуская бота с сервера в Китае или через прокси),
    явно включите переменную окружения:

        ENABLE_1688_ADAPTER=1

    Пока это не сделано, `search()` сразу возвращает пустой список,
    не отправляя ни одного запроса.
    """

    name = "1688"
    supported_regions = {"CN"}

    SEARCH_URL = "https://s.1688.com/selloffer/offer_search.htm"

    _PRICE_RE = re.compile(r"[\d][\d,\.]*")

    def __init__(
        self,
        max_results: int = 10,
        timeout: int = 12,
        enabled: Optional[bool] = None,
    ) -> None:
        self.max_results = max_results
        self.timeout = timeout
        self.enabled = (
            enabled
            if enabled is not None
            else os.getenv("ENABLE_1688_ADAPTER") == "1"
        )

    def search(
        self,
        queries: list[str],
        region: str,
        currency: str,
        budget: Optional[dict[str, Any]] = None,
    ) -> list[dict[str, Any]]:

        if not self.enabled:
            logger.info(
                "1688 adapter skipped: disabled by default "
                "(set ENABLE_1688_ADAPTER=1 to try it)",
            )
            return []

        all_offers: list[dict[str, Any]] = []

        for query in queries:
            try:
                offers = self._search_query(query=query, region=region)
            except Exception:
                logger.warning(
                    "1688 query failed: %s",
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
            params={"keywords": query},
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
        cards = soup.select("a[href*='detail.1688.com']")

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
            "source": "1688",
            "title": title,
            "brand": None,
            "category": None,
            "product_type": None,
            "model": None,
            "attributes": {},
            "product": product_data,
            "price": price,
            "currency": "CNY",
            "delivery": None,
            "taxes": None,
            "duties": None,
            "fees": None,
            "url": url,
            "seller": "1688 supplier",
            "condition": "new",
            "availability": "in_stock",
            "region": region,
            "description": "Оптовая цена в юанях (1688.com), обычно от завода.",
            "extracted": False,
        }
