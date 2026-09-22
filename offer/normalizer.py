from typing import Any


def normalize_offers(
    offers: list[dict[str, Any]],
) -> list[dict[str, Any]]:

    normalized = []

    for offer in offers:

        raw_price = offer.get("price")

        price = None

        if raw_price is not None:
            try:
                price = float(raw_price)
            except (TypeError, ValueError):
                price = None

        delivery = _to_float_or_none(
            offer.get("delivery")
        )

        taxes = _to_float_or_none(
            offer.get("taxes")
        )

        duties = _to_float_or_none(
            offer.get("duties")
        )

        fees = _to_float_or_none(
            offer.get("fees")
        )

        normalized_offer = {
            **offer,

            "price": price,

            "delivery": delivery,
            "taxes": taxes,
            "duties": duties,
            "fees": fees,

            "price_known": (
                price is not None
            ),

            "delivery_known": (
                delivery is not None
            ),

            "taxes_known": (
                taxes is not None
            ),

            "duties_known": (
                duties is not None
            ),

            "fees_known": (
                fees is not None
            ),
        }

        normalized.append(
            normalized_offer
        )

    return normalized


def _to_float_or_none(
    value: Any,
):
    if value is None:
        return None

    try:
        return float(value)
    except (TypeError, ValueError):
        return None