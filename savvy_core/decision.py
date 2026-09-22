from .models import Offer


def calculate_score(offer: Offer) -> int:
    """
    Предварительный SAVVY Score.

    Сейчас учитываем:
    - рейтинг продавца;
    - скорость доставки.

    Позже добавим:
    - историю цены;
    - качество отзывов;
    - надёжность продавца;
    - возврат;
    - гарантию;
    - риск;
    - соответствие запросу пользователя.
    """

    score = 50

    # Надёжность продавца
    if offer.seller_rating is not None:
        score += int(offer.seller_rating * 8)

    # Доставка
    if offer.delivery_days is not None:

        if offer.delivery_days <= 3:
            score += 8

        elif offer.delivery_days <= 7:
            score += 4

        elif offer.delivery_days > 14:
            score -= 5

    return max(0, min(100, score))


def choose_best_deal(
    offers: list[Offer],
) -> Offer | None:

    if not offers:
        return None

    return max(
        offers,
        key=calculate_score,
    )


def make_decision(
    offer: Offer | None,
) -> str:

    if offer is None:
        return "NO_RESULT"

    score = calculate_score(offer)

    if score >= 80:
        return "BUY"

    if score >= 60:
        return "WAIT"

    return "SKIP"


def explain_decision(
    offer: Offer | None,
    decision: str,
) -> str:

    if offer is None:
        return "Подходящих предложений не найдено."

    score = calculate_score(offer)

    return (
        f"SAVVY Score: {score}/100. "
        f"Решение: {decision}. "
        f"Полная стоимость: "
        f"{offer.real_cost:.2f} "
        f"{offer.currency}. "
        f"Продавец: {offer.seller}."
    )