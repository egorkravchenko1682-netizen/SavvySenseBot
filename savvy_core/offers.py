from .models import Offer, SearchRequest


def calculate_real_cost(offer: Offer) -> float:
    """
    Полная стоимость товара.

    Цена + доставка + налоги + обязательные сборы.
    """

    return (
        offer.price
        + offer.shipping_cost
        + offer.taxes
        + offer.fees
    )


def filter_offers(
    offers: list[Offer],
    request: SearchRequest,
) -> list[Offer]:

    result = []

    for offer in offers:

        if not offer.available:
            continue

        real_cost = calculate_real_cost(offer)

        if request.max_price is not None:
            if real_cost > request.max_price:
                continue

        result.append(offer)

    return result


def sort_by_real_cost(
    offers: list[Offer],
) -> list[Offer]:

    return sorted(
        offers,
        key=calculate_real_cost,
    )


def cheapest_offer(
    offers: list[Offer],
) -> Offer | None:

    if not offers:
        return None

    return min(
        offers,
        key=calculate_real_cost,
    )