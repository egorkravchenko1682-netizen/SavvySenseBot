from typing import Any


def calculate_real_cost(
    offer: dict[str, Any],
    target_currency: str,
    converter,
) -> dict[str, Any]:
    """
    Рассчитывает реальную стоимость предложения.

    Принцип SAVVY SENSE:

    UNKNOWN != 0

    Если дополнительный расход неизвестен,
    он не считается бесплатным.

    Возвращаются:

        total_cost
            Полная подтверждённая стоимость.
            None, если хотя бы один обязательный
            компонент неизвестен.

        partial_total_cost
            Стоимость на основании известных
            компонентов.

        cost_complete
            True, если все компоненты известны.

        cost_breakdown
            Подробная структура стоимости.
    """

    price = _to_float_or_none(
        offer.get("price")
    )

    if price is None:

        return {
            **offer,

            "total_cost": None,

            "partial_total_cost": None,

            "total_currency":
                target_currency,

            "cost_known": False,

            "cost_complete": False,

            "cost_breakdown": {
                "price": None,
                "delivery": None,
                "taxes": None,
                "duties": None,
                "fees": None,
            },
        }

    source_currency = (
        offer.get("currency")
        or target_currency
    )

    delivery, delivery_known = (
        _get_cost_component(
            offer,
            "delivery",
        )
    )

    taxes, taxes_known = (
        _get_cost_component(
            offer,
            "taxes",
        )
    )

    duties, duties_known = (
        _get_cost_component(
            offer,
            "duties",
        )
    )

    fees, fees_known = (
        _get_cost_component(
            offer,
            "fees",
        )
    )

    # ---------------------------------------------------------
    # PARTIAL COST
    # ---------------------------------------------------------

    partial_subtotal = price

    if delivery_known:
        partial_subtotal += delivery

    if taxes_known:
        partial_subtotal += taxes

    if duties_known:
        partial_subtotal += duties

    if fees_known:
        partial_subtotal += fees

    # ---------------------------------------------------------
    # CURRENCY CONVERSION
    # ---------------------------------------------------------

    try:

        partial_total_cost = (
            converter.convert(
                amount=partial_subtotal,
                from_currency=source_currency,
                to_currency=target_currency,
            )
        )

    except Exception:

        if (
            source_currency
            == target_currency
        ):

            partial_total_cost = (
                partial_subtotal
            )

        else:

            partial_total_cost = None

    # ---------------------------------------------------------
    # COMPLETE COST
    # ---------------------------------------------------------

    cost_complete = all(
        (
            delivery_known,
            taxes_known,
            duties_known,
            fees_known,
        )
    )

    total_cost = (
        partial_total_cost
        if cost_complete
        else None
    )

    return {
        **offer,

        "total_cost":
            total_cost,

        "partial_total_cost":
            partial_total_cost,

        "total_currency":
            target_currency,

        "cost_known":
            total_cost is not None,

        "cost_complete":
            cost_complete,

        "cost_breakdown": {

            "price":
                price,

            "delivery":
                delivery
                if delivery_known
                else None,

            "taxes":
                taxes
                if taxes_known
                else None,

            "duties":
                duties
                if duties_known
                else None,

            "fees":
                fees
                if fees_known
                else None,
        },

        "cost_known_components": {
            "price": True,
            "delivery":
                delivery_known,
            "taxes":
                taxes_known,
            "duties":
                duties_known,
            "fees":
                fees_known,
        },
    }


def calculate_offers_real_cost(
    offers: list[dict[str, Any]],
    target_currency: str,
    converter,
) -> list[dict[str, Any]]:
    """
    Рассчитывает стоимость всех предложений.
    """

    return [
        calculate_real_cost(
            offer=offer,
            target_currency=target_currency,
            converter=converter,
        )
        for offer in offers
    ]


def _get_cost_component(
    offer: dict[str, Any],
    name: str,
) -> tuple[float, bool]:
    """
    Возвращает:

        (value, known)

    Важно:

        отсутствующее значение = UNKNOWN

    а не 0.

    Явный 0 считается известным значением.

    Например:

        delivery=0
        → доставка бесплатная

        delivery=None
        → стоимость доставки неизвестна
    """

    value = offer.get(
        name
    )

    known_key = (
        f"{name}_known"
    )

    if known_key in offer:

        known = bool(
            offer.get(
                known_key
            )
        )

        if not known:
            return 0.0, False

    numeric = _to_float_or_none(
        value
    )

    if numeric is None:

        return 0.0, False

    return numeric, True


def _to_float_or_none(
    value: Any,
) -> float | None:

    if value is None:
        return None

    if isinstance(
        value,
        bool,
    ):
        return None

    try:

        return float(value)

    except (
        TypeError,
        ValueError,
    ):

        return None