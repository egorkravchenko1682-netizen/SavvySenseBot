from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)


def sweep_regions(
    search_engine: Any,
    queries: list[str],
    regions: list[str],
    currency: str,
    budget: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """
    Опрашивает `search_engine` отдельно по каждому региону из `regions`
    и объединяет результаты в один список.

    Каждому результату, у которого адаптер не проставил свой "region",
    присваивается регион, с которым он был запрошен — иначе дальнейшее
    сравнение "дешевле в другом регионе" в `region.logistics` было бы
    невозможным.

    Один упавший регион не должен останавливать остальные — тот же
    принцип отказоустойчивости, что и в `GlobalSearchEngine`.
    """

    if not queries:
        return []

    all_results: list[dict[str, Any]] = []

    for region in regions:
        try:
            results = search_engine.search(
                queries=queries,
                region=region,
                currency=currency,
                budget=budget or {},
            )
        except Exception:
            logger.warning(
                "Region sweep failed for %s",
                region,
                exc_info=True,
            )
            continue

        for result in results:
            if isinstance(result, dict) and not result.get("region"):
                result = {**result, "region": region}
            all_results.append(result)

    return all_results
