from typing import Any


def calculate_real_cost(
    offer: dict[str, Any],
    target_currency: str,
    converter,
) -> dict[str, Any]:
    """
    Рассчитывает полную стоимость одного предложения.

    Если цена неизвестна, total_cost остаётся None.
    """

    price = offer.get("price")

    if price is None:

        return {
            **offer,

            "total_cost": None,

            "total_currency":
                target_currency,

            "cost_known": False,

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

    delivery = (
        offer.get("delivery")
        or 0
    )

    taxes = (
        offer.get("taxes")
        or 0
    )

    duties = (
        offer.get("duties")
        or 0
    )

    fees = (
        offer.get("fees")
        or 0
    )

    subtotal = (
        float(price)
        + float(delivery)
        + float(taxes)
        + float(duties)
        + float(fees)
    )

    try:

        total_cost = converter.convert(
            amount=subtotal,
            from_currency=source_currency,
            to_currency=target_currency,
        )

    except Exception:

        if (
            source_currency
            == target_currency
        ):
            total_cost = subtotal

        else:
            total_cost = None

    return {
        **offer,

        "total_cost": total_cost,

        "total_currency":
            target_currency,

        "cost_known":
            total_cost is not None,

        "cost_breakdown": {
            "price": float(price),
            "delivery": float(delivery),
            "taxes": float(taxes),
            "duties": float(duties),
            "fees": float(fees),
        },
    }


def calculate_offers_real_cost(
    offers: list[dict[str, Any]],
    target_currency: str,
    converter,
) -> list[dict[str, Any]]:
    """
    Рассчитывает полную стоимость всех предложений.
    """

    return [
        calculate_real_cost(
            offer=offer,
            target_currency=target_currency,
            converter=converter,
        )
        for offer in offers
    ]