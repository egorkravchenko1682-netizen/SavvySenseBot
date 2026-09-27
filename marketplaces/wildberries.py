from __future__ import annotations

import logging
from typing import Any, Optional

import requests

logger = logging.getLogger(__name__)


class WildberriesAdapter:
    """
    Поиск по Wildberries (используется покупателями в Беларуси и
    России) через их публичный поисковый endpoint.

    ВАЖНО — честно о рисках неофициальной интеграции:
    У Wildberries нет официального публичного API для поиска товаров
    сторонними приложениями. Этот адаптер обращается к тому же
    JSON-эндпоинту, который использует сам сайт wildberries.ru в
    браузере (`search.wb.ru`). Это открытый, не требующий ключа
    endpoint, которым пользуется множество сторонних инструментов, но:

    - Wildberries может изменить путь/версию API (`v9` и т.п.) или
      формат ответа без предупреждения — тогда парсинг ниже перестанет
      работать, пока его не обновят под новую версию;
    - при слишком частых запросах Wildberries может начать возвращать
      ошибки/капчу для IP-адреса сервера.

    Поэтому вся логика обёрнута в try/except на уровне каждого
    запроса: если Wildberries недоступен или поменял формат, адаптер
    просто вернёт пустой список для этого запроса — как и предписывает
    `GlobalSearchEngine` для любого падающего источника — а не уронит
    весь пайплайн.
    """

    name = "wildberries"

    # Wildberries обслуживает и Беларусь, и Россию с одного каталога.
    supported_regions = {"BY", "RU"}

    SEARCH_URL = "https://search.wb.ru/exactmatch/ru/common/v9/search"

    # Числовой код склада/региона доставки, который WB ожидает в
    # параметре `dest` вместо буквенного кода страны. -1257786 —
    # общий центральный склад, разумное значение по умолчанию,
    # используемое большинством открытых интеграций.
    DEFAULT_DEST = -1257786

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
                    "Wildberries query failed: %s",
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

        params = {
            "appType": 1,
            "curr": "rub",
            "dest": self.DEFAULT_DEST,
            "query": query,
            "resultset": "catalog",
            "sort": "popular",
            "spp": 30,
        }

        response = requests.get(
            self.SEARCH_URL,
            params=params,
            timeout=self.timeout,
            headers={"User-Agent": "Mozilla/5.0 (SAVVY SENSE bot)"},
        )
        response.raise_for_status()

        payload = response.json()
        products = ((payload.get("data") or {}).get("products")) or []

        offers = []

        for product in products[: self.max_results]:
            offer = self._to_offer(product, region=region)
            if offer is not None:
                offers.append(offer)

        return offers

    @staticmethod
    def _to_offer(
        product: dict[str, Any],
        region: str,
    ) -> Optional[dict[str, Any]]:

        # Wildberries хранит цену в копейках, умноженную на 100
        # ("priceU"/"salePriceU" в их внутреннем формате).
        price_units = product.get("salePriceU") or product.get("priceU")

        if price_units is None:
            return None

        price = price_units / 100
        title = product.get("name")
        brand = product.get("brand")
        product_id = product.get("id")

        product_data = {
            "title": title,
            "brand": brand,
            "category": None,
            "product_type": None,
            "model": None,
            "attributes": {},
        }

        return {
            "source": "wildberries",
            "title": title,
            "brand": brand,
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
            "url": (
                f"https://www.wildberries.ru/catalog/{product_id}/detail.aspx"
                if product_id
                else None
            ),
            "seller": product.get("supplier") or "Wildberries",
            "condition": "new",
            "availability": (
                "in_stock"
                if (product.get("totalQuantity") or 1) > 0
                else "out_of_stock"
            ),
            "region": region,
            "description": None,
            "extracted": False,
            "rating": product.get("rating"),
            "reviews_count": product.get("feedbacks"),
        }
