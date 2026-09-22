from typing import Any


class GlobalSearchEngine:
    """
    Центральный движок глобального поиска SAVVY SENSE.

    Каждый источник подключается отдельным адаптером.
    Ошибка одного адаптера не должна останавливать
    остальные источники.
    """

    def __init__(
        self,
        adapters: list[Any] | None = None,
    ):

        self.adapters = adapters or []

    # =========================
    # ADD ADAPTER
    # =========================

    def add_adapter(
        self,
        adapter: Any,
    ):

        self.adapters.append(
            adapter
        )

    # =========================
    # SEARCH
    # =========================

    def search(
        self,
        queries: list[str],
        region: str,
        currency: str,
        budget: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:

        all_offers = []

        for adapter in self.adapters:

            adapter_name = getattr(
                adapter,
                "name",
                "unknown",
            )

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

                    print(
                        f"Search adapter "
                        f"{adapter_name}: "
                        f"{len(offers)} results"
                    )

                else:

                    print(
                        f"Search adapter "
                        f"{adapter_name}: "
                        f"0 results"
                    )

            except Exception as error:

                print(
                    f"Search adapter "
                    f"{adapter_name} "
                    f"failed: {error}"
                )

        return all_offers