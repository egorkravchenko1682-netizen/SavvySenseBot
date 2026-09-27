import logging
from typing import Any

logger = logging.getLogger(__name__)


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

            if not self._adapter_applies(adapter, region):

                logger.info(
                    "Search adapter %s: skipped (not relevant for region %s)",
                    adapter_name,
                    region,
                )

                continue

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

                    logger.info(
                        "Search adapter %s: %d results",
                        adapter_name,
                        len(offers),
                    )

                else:

                    logger.info(
                        "Search adapter %s: 0 results",
                        adapter_name,
                    )

            except Exception:

                logger.warning(
                    "Search adapter %s failed",
                    adapter_name,
                    exc_info=True,
                )

        return all_offers

    @staticmethod
    def _adapter_applies(adapter: Any, region: str) -> bool:
        """
        Определяет, стоит ли опрашивать конкретный адаптер для
        данного региона.

        Маркетплейсы (Wildberries, Ozon, AliExpress и т.д.) обычно
        актуальны только для части регионов — например, нет смысла
        спрашивать Wildberries при поиске в регионе "CN". Адаптер
        объявляет это через атрибут класса `supported_regions`
        (набор кодов регионов). Если атрибут отсутствует или равен
        `None` — адаптер считается универсальным (например,
        DuckDuckGoAdapter или DemoAdapter) и опрашивается всегда.
        """

        supported_regions = getattr(adapter, "supported_regions", None)

        if not supported_regions:
            return True

        return (region or "").upper() in supported_regions