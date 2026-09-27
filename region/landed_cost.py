from __future__ import annotations

from typing import Any

_COST_COMPONENTS = ("delivery", "taxes", "duties", "fees")


def apply_real_cost(offer: dict[str, Any]) -> dict[str, Any]:
    """
    Считает полную (landed) стоимость оффера: price + доставка + налоги
    + пошлина + комиссии, в валюте самого оффера (после нормализации
    через `offer.normalizer` и оценки через `region.logistics` все
    компоненты уже в одной валюте — валюте оффера).

    Пишет результат в `real_cost` / `real_cost_currency` /
    `real_cost_known` — это те самые поля, которые уже читает
    `offer.offer_comparator.OfferComparator` (использующийся внутри
    `DealEngine`). Так внутри DealEngine ничего не пришлось менять:
    он просто начинает сравнивать предложения по полной стоимости,
    как только она известна.

    Принцип SAVVY SENSE (UNKNOWN != 0) соблюдён: если хотя бы один
    компонент не известен, `real_cost_known = False`, и сравнение
    в DealEngine автоматически откатывается к сравнению по голой цене
    (`price`) — это не даёт скрытым доставке/пошлине "молча" стать
    нулём.
    """

    price = offer.get("price")

    if price is None:
        return {
            **offer,
            "real_cost": None,
            "real_cost_currency": None,
            "real_cost_known": False,
            "real_cost_breakdown": None,
        }

    total = float(price)
    breakdown: dict[str, Any] = {"price": price}
    all_known = True

    for component in _COST_COMPONENTS:
        value = offer.get(component)
        known = bool(offer.get(f"{component}_known"))

        if known and value is not None:
            breakdown[component] = value
            total += float(value)
        else:
            breakdown[component] = None
            all_known = False

    return {
        **offer,
        "real_cost": total if all_known else None,
        "real_cost_currency": offer.get("currency") if all_known else None,
        "real_cost_known": all_known,
        "real_cost_breakdown": breakdown,
        # Частичная сумма всегда полезна для отображения пользователю,
        # даже когда не все компоненты известны — с пометкой, что это
        # НЕ гарантированный итог.
        "real_cost_partial": total,
    }


def apply_real_cost_to_offers(offers: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [apply_real_cost(offer) for offer in offers]
