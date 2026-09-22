from typing import Any


class DemoAdapter:
    """
    Тестовый адаптер.

    Нужен только для проверки архитектуры
    Global Search Engine.

    Реальные маркетплейсы подключаются
    отдельными адаптерами.
    """

    name = "demo"

    def search(
        self,
        queries: list[str],
        region: str,
        currency: str,
        budget: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:

        budget = budget or {}

        max_price = budget.get("max")

        price = 699.99

        if max_price is not None:
            price = min(price, float(max_price))

        return [
            {
                "source": self.name,
                "title": "Apple iPhone 15 Pro Max 256 GB",
                "brand": "Apple",
                "category": "smartphone",
                "price": price,
                "currency": currency,
                "delivery": None,
                "url": None,
                "seller": "SAVVY Demo",
                "condition": "new",
                "region": region,
            }
        ]