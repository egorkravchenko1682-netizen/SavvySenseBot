from __future__ import annotations

from typing import Any, Optional

from currency.converter import CurrencyConverter
from .groups import EAEU_REGIONS

# ---------------------------------------------------------------------
# ЭВРИСТИКИ ДОСТАВКИ И ПОШЛИН
#
# Это ОЦЕНКИ, а не тарифы конкретного перевозчика или официальная
# налоговая консультация. Они используются только тогда, когда сам
# оффер (продавец / OfferExtractor) не сообщил реальную стоимость
# доставки или пошлины — реальные данные всегда имеют приоритет.
#
# Значения — в USD, конвертируются в валюту оффера через
# CurrencyConverter. Числа легко скорректировать под реальные тарифы
# по мере подключения настоящих курьерских служб/таможенных API —
# остальной код (`estimate_logistics`, DealEngine) менять не придётся.
# ---------------------------------------------------------------------

_SHIPPING_USD_BY_ROUTE = {
    "domestic": 3.0,  # доставка внутри одной страны
    "eaeu_cross_border": 8.0,  # между странами ЕАЭС (BY/RU/KZ/AM/KG)
    "cis_other": 12.0,  # СНГ вне ЕАЭС (UZ/AZ/TJ/MD) или в них
    "china_international": 6.0,  # международная посылка из Китая
    "world_international": 15.0,  # остальной мир
}

# Правило личного ввоза для стран ЕАЭС (упрощённо): посылки из-за
# пределов ЕАЭС дороже порога облагаются пошлиной. Реальные правила
# учитывают ещё и вес (кг/мес.) и накопительный лимit за календарный
# месяц — здесь это не отслеживается, поэтому пошлина — грубая оценка
# на один заказ, а не гарантированная сумма таможни.
_EAEU_DUTY_FREE_THRESHOLD_EUR = 200.0
_EAEU_DUTY_RATE_ABOVE_THRESHOLD = 0.15


def classify_route(source_region: str, destination_region: str) -> str:
    source_region = (source_region or destination_region or "").upper()
    destination_region = (destination_region or source_region or "").upper()

    if source_region == destination_region:
        return "domestic"

    if source_region in EAEU_REGIONS and destination_region in EAEU_REGIONS:
        return "eaeu_cross_border"

    if source_region == "CN":
        return "china_international"

    if source_region in {"BY", "RU", "KZ", "UZ", "KG", "AM", "AZ", "TJ", "MD"}:
        return "cis_other"

    return "world_international"


def estimate_logistics(
    offer: dict[str, Any],
    destination_region: str,
    converter: Optional[CurrencyConverter] = None,
) -> dict[str, Any]:
    """
    Дополняет оффер оценкой доставки и пошлины, ЕСЛИ они ещё неизвестны.

    Реальные значения (уже пришедшие из OfferExtractor/адаптера) никогда
    не перезаписываются. Там, где пришлось оценивать самостоятельно,
    выставляется флаг `<поле>_estimated = True`, чтобы UI мог показать
    пользователю "≈" вместо точной суммы.
    """

    converter = converter or CurrencyConverter()

    result = dict(offer)

    source_region = (result.get("region") or destination_region or "US").upper()
    destination_region = (destination_region or source_region).upper()
    currency = result.get("currency") or "USD"

    route = classify_route(source_region, destination_region)

    if result.get("delivery") is None:
        shipping_usd = _SHIPPING_USD_BY_ROUTE[route]

        try:
            shipping = converter.convert(shipping_usd, "USD", currency)
        except ValueError:
            shipping = None

        if shipping is not None:
            result["delivery"] = shipping
            result["delivery_known"] = True
            result["delivery_estimated"] = True

    if result.get("duties") is None:
        duty = _estimate_duty(
            price=result.get("price"),
            currency=currency,
            source_region=source_region,
            destination_region=destination_region,
            converter=converter,
        )

        if duty is not None:
            result["duties"] = duty
            result["duties_known"] = True
            result["duties_estimated"] = True

    # "taxes" и "fees" — в отличие от доставки и пошлины — для
    # частной покупки обычно уже включены площадкой в отображаемую
    # цену (НДС маркетплейса, комиссия платежи) или отсутствуют.
    # Пошлина (duties) — единственный компонент, который действительно
    # стоит отдельно оценивать: он может быть существенным и не виден
    # в цене товара. Если оффер сам не заявил отдельных налогов/сборов,
    # считаем их нулевыми (а не "неизвестными") — иначе
    # `real_cost_known` никогда не станет True, и сравнение "с учётом
    # всех расходов" в DealEngine не будет работать ни для одного
    # предложения.
    if result.get("taxes") is None:
        result["taxes"] = 0.0
        result["taxes_known"] = True
        result["taxes_estimated"] = True

    if result.get("fees") is None:
        result["fees"] = 0.0
        result["fees_known"] = True
        result["fees_estimated"] = True

    return result


def _estimate_duty(
    price: Optional[float],
    currency: str,
    source_region: str,
    destination_region: str,
    converter: CurrencyConverter,
) -> Optional[float]:

    if price is None:
        return None

    # За пределами ЕАЭС таможенные правила сильно различаются по стране —
    # честнее оставить пошлину неизвестной, чем угадывать цифру.
    if destination_region not in EAEU_REGIONS:
        return None

    # Свободное перемещение товаров внутри ЕАЭС — пошлины нет.
    if source_region in EAEU_REGIONS:
        return 0.0

    try:
        price_eur = converter.convert(price, currency, "EUR")
    except ValueError:
        return None

    if price_eur <= _EAEU_DUTY_FREE_THRESHOLD_EUR:
        return 0.0

    excess_eur = price_eur - _EAEU_DUTY_FREE_THRESHOLD_EUR
    duty_eur = excess_eur * _EAEU_DUTY_RATE_ABOVE_THRESHOLD

    try:
        return converter.convert(duty_eur, "EUR", currency)
    except ValueError:
        return None
