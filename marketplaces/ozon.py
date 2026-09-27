from __future__ import annotations

import json
import logging
from typing import Any, Optional

import requests

logger = logging.getLogger(__name__)


class OzonAdapter:
    """
    Поиск по Ozon через их внутренний "composer" JSON-эндпоинт,
    которым пользуется сам сайт при серверном рендеринге страницы
    поиска.

    ЧЕСТНОЕ ПРЕДУПРЕЖДЕНИЕ — это наименее надёжный адаптер в проекте:
    - у Ozon нет публичного API поиска для сторонних приложений;
    - "composer-api" — их внутренний формат, структура ответа
      (widgetStates -> вложенный JSON по ключу searchResultsV2)
      регулярно меняется вместе с версткой сайта;
    - Ozon активно защищается от автоматических запросов
      (антибот-проверки), поэтому в проде этот адаптер может
      систематически возвращать пустой список даже при верном коде —
      тогда для Ozon стоит рассмотреть платный доступ к данным через
      партнёрские сервисы (например, Ozon Seller API покрывает только
      собственные товары продавца, не общий каталог).

    Если разбор ответа не удался — адаптер по архитектуре проекта
    просто возвращает пустой список для этого запроса, не поднимая
    исключение наружу (см. `GlobalSearchEngine`).
    """

    name = "ozon"
    supported_regions = {"RU"}

    SEARCH_URL = "https://www.ozon.ru/api/composer-api.bx/page/json/v2"

    def __init__(
        self,
        max_results: int = 10,
        timeout: int = 10,
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
                    "Ozon query failed: %s",
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

        params = {"url": f"/search/?text={query}&from_global=true"}

        response = requests.get(
            self.SEARCH_URL,
            params=params,
            timeout=self.timeout,
            headers={
                "User-Agent": "Mozilla/5.0 (SAVVY SENSE bot)",
                "Accept": "application/json",
            },
        )
        response.raise_for_status()

        payload = response.json()
        items = self._extract_items(payload)

        offers = []
        for item in items[: self.max_results]:
            offer = self._to_offer(item, region=region)
            if offer is not None:
                offers.append(offer)

        return offers

    @staticmethod
    def _extract_items(payload: dict[str, Any]) -> list[dict[str, Any]]:
        """
        Ищет карточки товаров внутри `widgetStates`.

        Формат ответа Ozon — набор виджетов, где нужный нам виджет
        поиска (обычно с ключом, начинающимся на "searchResultsV2")
        хранит СВОЮ JSON-строку как значение (а не вложенный объект),
        поэтому её нужно распарсить отдельно.
        """

        widget_states = payload.get("widgetStates") or {}

        for key, value in widget_states.items():
            if not key.startswith("searchResultsV2"):
                continue

            try:
                widget_data = json.loads(value)
            except (TypeError, ValueError):
                continue

            items = widget_data.get("items") or []
            if items:
                return items

        return []

    @staticmethod
    def _to_offer(
        item: dict[str, Any],
        region: str,
    ) -> Optional[dict[str, Any]]:

        main_state = item.get("mainState") or []

        title = None
        price = None

        for block in main_state:
            atom = block.get("atom") or {}

            if block.get("id") == "name" or "textAtom" in atom:
                title = title or (atom.get("textAtom") or {}).get("text")

            if "priceV2" in atom:
                price_texts = (atom.get("priceV2") or {}).get("price") or []
                for price_text in price_texts:
                    text_value = price_text.get("text")
                    if text_value:
                        price = _parse_price_text(text_value)
                        break

        if price is None:
            return None

        link = item.get("action", {}).get("link")
        url = f"https://www.ozon.ru{link}" if link else None

        product_data = {
            "title": title,
            "brand": None,
            "category": None,
            "product_type": None,
            "model": None,
            "attributes": {},
        }

        return {
            "source": "ozon",
            "title": title,
            "brand": None,
            "category": None,
            "product_type": None,
            "model": None,
            "attributes": {},
            "product": product_data,
            "price": price,
            "currency": "RUB",
            "delivery": None,
            "taxes": None,
            "duties": None,
            "fees": None,
            "url": url,
            "seller": "Ozon",
            "condition": "new",
            "availability": "in_stock",
            "region": region,
            "description": None,
            "extracted": False,
        }


def _parse_price_text(text: str) -> Optional[float]:
    digits = "".join(ch for ch in text if ch.isdigit())
    if not digits:
        return None
    try:
        return float(digits)
    except ValueError:
        return None
