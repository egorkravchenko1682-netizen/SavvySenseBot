from typing import Any


def _to_float(value: Any) -> float:
    """
    Безопасно преобразует значение в число.
    """

    if value is None:
        return 0.0

    if isinstance(value, (int, float)):
        return float(value)

    try:
        cleaned = (
            str(value)
            .replace(",", ".")
            .replace("$", "")
            .replace("€", "")
            .replace("₽", "")
            .strip()
        )

        return float(cleaned)

    except (TypeError, ValueError):
        return 0.0


def normalize_offer(
    offer: dict[str, Any],
) -> dict[str, Any]:
    """
    Приводит предложение любого адаптера
    к единому формату SAVVY.
    """

    price = _to_float(
        offer.get("price")
    )

    delivery = _to_float(
        offer.get("delivery")
    )

    taxes = _to_float(
        offer.get("taxes")
    )

    duties = _to_float(
        offer.get("duties")
    )

    fees = _to_float(
        offer.get("fees")
    )

    total_cost = (
        price
        + delivery
        + taxes
        + duties
        + fees
    )

    return {
        "product": {
            "title": offer.get(
                "title"
            ),
            "brand": offer.get(
                "brand"
            ),
            "category": offer.get(
                "category"
            ),
        },

        "source": offer.get(
            "source"
        ),

        "seller": offer.get(
            "seller"
        ),

        "price": price,

        "currency": offer.get(
            "currency",
            "USD",
        ),

        "delivery": delivery,

        "taxes": taxes,

        "duties": duties,

        "fees": fees,

        "total_cost": round(
            total_cost,
            2,
        ),

        "condition": offer.get(
            "condition",
            "unknown",
        ),

        "availability": offer.get(
            "availability",
            "unknown",
        ),

        "region": offer.get(
            "region"
        ),

        "url": offer.get(
            "url"
        ),
    }


def normalize_offers(
    offers: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """
    Нормализует список предложений.
    """

    normalized = []

    for offer in offers:

        try:

            normalized.append(
                normalize_offer(
                    offer
                )
            )

        except Exception as error:

            print(
                f"Offer normalization "
                f"failed: {error}"
            )

    return normalized