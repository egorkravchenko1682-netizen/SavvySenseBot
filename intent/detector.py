from typing import Optional


def detect_intent(
    text: Optional[str] = None,
    input_type: Optional[str] = None,
) -> str:
    """
    Определяет основное намерение пользователя
    без использования внешних AI/API.
    """

    # URL
    if input_type == "url":
        return "product_search"

    # Фото
    if input_type == "photo":
        return "product_search"

    # Нет текста
    if not text:
        return "unknown"

    text = text.lower().strip()

    # Сравнение
    compare_words = (
        "сравни",
        "сравнить",
        "сравнение",
        "что лучше",
        "какой лучше",
    )

    if any(word in text for word in compare_words):
        return "compare"

    # Поиск дешевле
    cheaper_words = (
        "дешевле",
        "дешевый",
        "дешёвый",
        "найди дешевле",
        "где дешевле",
    )

    if any(word in text for word in cheaper_words):
        return "cheaper"

    # Проверка покупки
    check_words = (
        "стоит ли",
        "выгодно ли",
        "выгодно",
        "проверить товар",
        "проверить цену",
    )

    if any(word in text for word in check_words):
        return "check"

    # Отслеживание цены
    track_words = (
        "следи",
        "отслеживай",
        "отследи",
        "следить за ценой",
        "отслеживать цену",
    )

    if any(word in text for word in track_words):
        return "track"

    # По умолчанию — поиск товара
    return "product_search"