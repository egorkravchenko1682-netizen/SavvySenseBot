from typing import Any


def calculate_offers_real_cost(
    offers: list[dict[str, Any]],
    target_currency: str,
    converter,
) -> list[dict[str, Any]]:

    result = []

    for offer in offers:

        price = offer.get("price")

        price_known = (
            price is not None
        )

        if not price_known:

            result.append(
                {
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
            )

            continue

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
                from_currency=(
                    source_currency
                ),
                to_currency=(
                    target_currency
                ),
            )

        except Exception:

            total_cost = (
                subtotal
                if source_currency
                == target_currency
                else None
            )

        result.append(
            {
                **offer,

                "total_cost":
                    total_cost,

                "total_currency":
                    target_currency,

                "cost_known":
                    total_cost is not None,

                "cost_breakdown": {
                    "price": price,
                    "delivery": delivery,
                    "taxes": taxes,
                    "duties": duties,
                    "fees": fees,
                },
            }
        )

    return result