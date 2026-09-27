from __future__ import annotations

from typing import Any, Optional

from currency.converter import CurrencyConverter

# Поля с денежными суммами, которые нужно привести к единой валюте,
# прежде чем сравнивать предложения из разных площадок/регионов.
_MONEY_FIELDS = ("price", "delivery", "taxes", "duties", "fees")


def normalize_offer_currency(
    offer: dict[str, Any],
    target_currency: str,
    converter: Optional[CurrencyConverter] = None,
) -> dict[str, Any]:
    """
    Приводит все денежные поля оффера к единой валюте.

    Без этого шага `offer.offer_comparator.OfferComparator` не может
    сравнить, например, предложение с Wildberries (RUB) и предложение
    с eBay (USD) — он специально отказывается сравнивать суммы в
    разных валютах, а не молча считает курс 1:1. Здесь конвертация
    происходит один раз, сразу после нормализации оффера, поэтому
    весь дальнейший пайплайн (оценка логистики, DealEngine) работает
    в одной валюте — валюте, которую попросил пользователь.
    """

    converter = converter or CurrencyConverter()

    source_currency = offer.get("currency") or target_currency

    result = dict(offer)

    if (
        not source_currency
        or converter.normalize_currency(source_currency)
        == converter.normalize_currency(target_currency)
    ):
        result["currency"] = target_currency
        return result

    for field in _MONEY_FIELDS:
        value = result.get(field)

        if value is None:
            continue

        try:
            result[field] = converter.convert(
                value,
                source_currency,
                target_currency,
            )
        except ValueError:
            # Валюта, которую конвертер не знает — честнее объявить
            # компонент снова неизвестным, чем оставить число в чужой
            # валюте под видом целевой.
            result[field] = None
            result[f"{field}_known"] = False

    result["currency"] = target_currency
    result["original_currency"] = source_currency

    return result


def normalize_offers_currency(
    offers: list[dict[str, Any]],
    target_currency: str,
    converter: Optional[CurrencyConverter] = None,
) -> list[dict[str, Any]]:
    converter = converter or CurrencyConverter()

    return [
        normalize_offer_currency(offer, target_currency, converter)
        for offer in offers
    ]
