from typing import Any, Optional

from currency.converter import CurrencyConverter


class DemoAdapter:
    """
    Тестовый источник SAVVY SENSE.

    Используется для проверки всей цепочки:
    Search -> Attribute Matching -> Cost -> Deal Engine.

    Цена намеренно немного отличается по регионам (см.
    `_REGION_PRICE_MULTIPLIER`) — это позволяет проверить
    кросс-региональное сравнение (`region.logistics`,
    `region.landed_cost`) без подключения реальных маркетплейсов.

    Для запроса про iPhone возвращается подробный фикстур с
    брендом/моделью/характеристиками (нужен для проверки строгого
    ProductMatcher). Для любого другого запроса (например, категорий
    из `gift.catalog`) — обобщённый оффер с названием из самого
    запроса, чтобы результат не выглядел абсурдно ("духи" -> "iPhone").

    Базовые цены фикстур заданы в USD и конвертируются в валюту,
    которую попросил вызывающий код (`currency`) — раньше число
    просто "переклеивалось" в другую валюту без конвертации, из-за
    чего, например, запрос в RUB получал цену вроде "39.99 RUB"
    (меньше доллара), которая не проходила ни по одному разумному
    бюджету после учёта доставки.

    В дальнейшем реальные маркетплейсы будут подключаться отдельными
    адаптерами (см. пакет `marketplaces/`).
    """

    name = "demo"

    # Насколько цена в конкретном регионе отличается от базовой —
    # только для демонстрации кросс-регионального сравнения.
    _REGION_PRICE_MULTIPLIER = {
        "CN": 0.78,
        "RU": 0.94,
        "WORLD": 0.97,
    }

    def __init__(
        self,
        currency_converter: Optional[CurrencyConverter] = None,
    ) -> None:
        self.currency_converter = currency_converter or CurrencyConverter()

    def search(
        self,
        queries: list[str],
        region: str,
        currency: str,
        budget: Optional[dict[str, Any]] = None,
    ) -> list[dict[str, Any]]:

        budget = budget or {}
        max_price = budget.get("max")

        query_text = (queries[0] if queries else "").strip()

        if "iphone" in query_text.lower():
            offer = self._iphone_fixture()
        else:
            offer = self._generic_fixture(query_text)

        price_usd = offer["price"]
        price_usd *= self._REGION_PRICE_MULTIPLIER.get(
            (region or "").upper(),
            1.0,
        )

        try:
            price = self.currency_converter.convert(price_usd, "USD", currency)
        except ValueError:
            # Незнакомая конвертеру валюта — остаёмся в USD, а не
            # выдаём число в неверной валюте под чужой меткой.
            price = price_usd
            currency = "USD"

        if max_price is not None:
            try:
                max_price = float(max_price)
                if max_price > 0:
                    # Оставляем немного запаса под доставку/пошлину,
                    # которые region.logistics добавит поверх цены —
                    # иначе демо-оффер, обрезанный ровно по бюджету,
                    # всегда будет казаться "превышающим бюджет" после
                    # учёта полной стоимости.
                    price = min(price, max_price * 0.7)
            except (TypeError, ValueError):
                pass

        offer["price"] = price
        offer["currency"] = currency
        offer["region"] = region

        return [offer]

    @staticmethod
    def _iphone_fixture() -> dict[str, Any]:
        return {
            "source": "demo",
            "title": "Apple iPhone 15 Pro Max 256 GB",
            "brand": "Apple",
            "category": "smartphone",
            "product_type": "smartphone",
            "model": "iPhone 15 Pro Max",
            "attributes": {
                "storage": "256 GB",
                "condition": "new",
            },
            "product": {
                "title": "Apple iPhone 15 Pro Max 256 GB",
                "brand": "Apple",
                "category": "smartphone",
                "product_type": "smartphone",
                "model": "iPhone 15 Pro Max",
                "attributes": {
                    "storage": "256 GB",
                    "condition": "new",
                },
            },
            "price": 699.99,
            "delivery": None,
            "taxes": None,
            "duties": None,
            "fees": None,
            "url": None,
            "seller": "SAVVY Demo",
            "condition": "new",
            "availability": "in_stock",
            "description": "Demo offer for SAVVY SENSE testing.",
            "extracted": False,
        }

    @staticmethod
    def _generic_fixture(query_text: str) -> dict[str, Any]:
        title = query_text.title() if query_text else "Demo Product"

        return {
            "source": "demo",
            "title": title,
            "brand": None,
            "category": None,
            "product_type": None,
            "model": None,
            "attributes": {},
            "product": {
                "title": title,
                "brand": None,
                "category": None,
                "product_type": None,
                "model": None,
                "attributes": {},
            },
            "price": 39.99,
            "delivery": None,
            "taxes": None,
            "duties": None,
            "fees": None,
            "url": None,
            "seller": "SAVVY Demo",
            "condition": "new",
            "availability": "in_stock",
            "description": "Demo offer for SAVVY SENSE testing.",
            "extracted": False,
        }
