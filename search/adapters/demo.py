from typing import Any


class DemoAdapter:
    """
    Тестовый источник SAVVY SENSE.

    Используется для проверки всей цепочки:
    Search -> Attribute Matching -> Cost -> Deal Engine.

    В дальнейшем реальные маркетплейсы будут подключаться
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

        max_price = budget.get(
            "max"
        )

        price = 699.99

        if max_price is not None:

            try:

                max_price = float(
                    max_price
                )

                if max_price > 0:
                    price = min(
                        price,
                        max_price,
                    )

            except (
                TypeError,
                ValueError,
            ):
                pass

        return [
            {
                "source": self.name,

                "title":
                    "Apple iPhone 15 Pro Max 256 GB",

                "brand":
                    "Apple",

                "category":
                    "smartphone",

                "product_type":
                    "smartphone",

                "model":
                    "iPhone 15 Pro Max",

                "attributes": {
                    "storage":
                        "256 GB",

                    "condition":
                        "new",
                },

                "product": {
                    "title":
                        "Apple iPhone 15 Pro Max 256 GB",

                    "brand":
                        "Apple",

                    "category":
                        "smartphone",

                    "product_type":
                        "smartphone",

                    "model":
                        "iPhone 15 Pro Max",

                    "attributes": {
                        "storage":
                            "256 GB",

                        "condition":
                            "new",
                    },
                },

                "price":
                    price,

                "currency":
                    currency,

                "delivery":
                    None,

                "taxes":
                    None,

                "duties":
                    None,

                "fees":
                    None,

                "url":
                    None,

                "seller":
                    "SAVVY Demo",

                "condition":
                    "new",

                "availability":
                    "in_stock",

                "region":
                    region,

                "description":
                    "Demo offer for SAVVY SENSE testing.",

                "extracted":
                    False,
            }
        ]