import re

from .models import SearchRequest, UserProfile


def detect_intent(text: str) -> str:
    query = text.lower()

    if any(word in query for word in [
        "подарок",
        "подарить",
        "для девушки",
        "для парня",
        "для жены",
        "для мужа",
        "для мамы",
        "для папы",
    ]):
        return "gift"

    if any(word in query for word in [
        "дешевле",
        "подешевле",
        "дешёвый",
        "дешевый",
        "аналог",
    ]):
        return "find_cheaper"

    if any(word in query for word in [
        "сравни",
        "сравнить",
        "сравнение",
    ]):
        return "compare"

    if any(word in query for word in [
        "стоит ли",
        "покупать",
        "брать",
    ]):
        return "buy_decision"

    if any(word in query for word in [
        "следить за ценой",
        "отслеживать цену",
        "уведомить о снижении",
    ]):
        return "price_watch"

    return "product_search"


def extract_budget(
    text: str,
) -> tuple[float | None, str | None]:

    query = text.lower()

    patterns = [
        (r"до\s+(\d+(?:[.,]\d+)?)\s*(byn|бел\.?\