from typing import Any


class GlobalSearchEngine:
    """
    Центральный движок глобального поиска.

    Движок не знает деталей конкретных
    маркетплейсов.

    Каждый источник подключается
    отдельным адаптером.
    """

    def __init__(
        self,
        adapters: list[Any] | None = None,
    ):

        self.adapters = adapters or []

    def add_adapter(
        self,
        adapter: Any,
    ):

        self.adapters.append(
            adapter
        )

    def search(
        self,
        queries: list[str],
        region: str,
        currency: str,
        budget: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:

        all_offers = []

        for adapter in self.adapters:

            try:

                offers = adapter.search(
                    queries=queries,
                    region=region,
                    currency=currency,
                    budget=budget,
                )

                if offers:
                    all_offers.extend(
                        offers
                    )

            except Exception as error:

                print(
                    f"Search adapter "
                    f"{getattr(adapter, 'name', 'unknown')} "
                    f"failed: {error}"
                )

        return all_offers