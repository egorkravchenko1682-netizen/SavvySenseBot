from typing import Any

from currency import CurrencyConverter


def _number(
    value: Any,
) -> float:

    if value is None:
        return 0.0

    if isinstance(
        value,
        (int, float),
    ):
        return float(value)

    try:
        return float(
            str(value)
            .replace(",", ".")
            .replace("$", "")
            .replace("€", "")
            .replace("₽", "")
            .strip()
        )

    except (
        TypeError,
        ValueError,
    ):
        return 0.0


def calculate_real_cost(
    offer: dict[str, Any],
    target_currency: str,
    converter: CurrencyConverter,
) -> dict[str, Any]:

    source_currency = (
        offer.get(
            "currency"
        )
        or "USD"
    )

    source_currency = (
        converter.normalize_currency(
            source_currency
        )
    )

    target_currency = (
        converter.normalize_currency(
            target_currency
        )
    )

    price = _number(
        offer.get("price")
    )

    delivery = _number(
        offer.get("delivery")
    )

    taxes = _number(
        offer.get("taxes")
    )

    duties = _number(
        offer.get("duties")
    )

    fees = _number(
        offer.get("fees")
    )

    subtotal = (
        price
        + delivery
        + taxes
        + duties
        + fees
    )

    total_cost = converter.convert(
        amount=subtotal,
        from_currency=source_currency,
        to_currency=target_currency,
    )

    return {
        "price": price,
        "delivery": delivery,
        "taxes": taxes,
        "duties": duties,
        "fees": fees,

        "source_currency":
            source_currency,

        "target_currency":
            target_currency,

        "subtotal":
            round(subtotal, 2),

        "total_cost":
            total_cost,
    }


def calculate_offers_real_cost(
    offers: list[dict[str, Any]],
    target_currency: str,
    converter: CurrencyConverter,
) -> list[dict[str, Any]]:

    result = []

    for offer in offers:

        try:

            cost = calculate_real_cost(
                offer=offer,
                target_currency=target_currency,
                converter=converter,
            )

            updated_offer = {
                **offer,

                "real_cost": cost,

                "total_cost":
                    cost["total_cost"],

                "total_currency":
                    cost["target_currency"],
            }

            result.append(
                updated_offer
            )

        except Exception as error:

            print(
                f"Real cost calculation "
                f"failed: {error}"
            )

            result.append(offer)

    return result