from products import Product


def calculate_deal_score(product: Product) -> int:
    score = 50

    # Цена
    if product.price is not None:
        score += 15

    # Рейтинг
    if product.rating is not None:
        if product.rating >= 4.8:
            score += 15
        elif product.rating >= 4.5:
            score += 10
        elif product.rating >= 4.0:
            score += 5

    # Количество отзывов
    if product.reviews is not None:
        if product.reviews >= 1000:
            score += 10
        elif product.reviews >= 100:
            score += 5

    # Точный товар
    if product.is_exact_match:
        score += 10

    return min(score, 100)


def deal_label(score: int) -> str:

    if score >= 90:
        return "🔥 ОЧЕНЬ ВЫГОДНО"

    if score >= 75:
        return "🟢 ВЫГОДНО"

    if score >= 60:
        return "🟡 НОРМАЛЬНО"

    return "🔴 НЕВЫГОДНО"