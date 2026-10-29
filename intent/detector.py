from typing import Optional
import re


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

    # Short social messages are conversation, not shopping queries. Keep
    # unknown product names searchable: only classify common non-shopping
    # phrases here instead of relying on a closed product vocabulary.
    normalized = re.sub(r"[!?.,\s]+", " ", text).strip()
    if re.fullmatch(
        r"(?:привет|здравствуй|здравствуйте|доброе утро|добрый день|добрый вечер|"
        r"как дела|как ты|что нового|спасибо|пока|hello|hi|hey|how are you|"
        r"good morning|good afternoon|good evening|thanks|thank you|bye|"
        r"сәлем|сәлеметсіз бе|қалайсың|қалыңыз қалай|рақмет|сау бол)"
        r"(?: (?:как дела|как ты|что нового|how are you|қалайсың|қалыңыз қалай))*",
        normalized,
    ):
        return "conversation"

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
