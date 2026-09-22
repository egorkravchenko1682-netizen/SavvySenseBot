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


def extract_budget(text: str):
    query = text.lower()

    patterns = [
        (r"до\s+(\d+(?:[.,]\d+)?)\s*(usd|\$)", "USD"),
        (r"до\s+(\d+(?:[.,]\d+)?)\s*(eur|€)", "EUR"),
        (r"до\s+(\d+(?:[.,]\d+)?)\s*(rub|₽)", "RUB"),
        (r"до\s+(\d+(?:[.,]\d+)?)\s*(byn)", "BYN"),
        (r"до\s+(\d+(?:[.,]\d+)?)\s*(kzt)", "KZT"),
        (r"до\s+(\d+(?:[.,]\d+)?)\s*(uzs)", "UZS"),
    ]

    for pattern, currency in patterns:
        match = re.search(pattern, query)

        if match:
            value = float(
                match.group(1).replace(",", ".")
            )
            return value, currency

    return None, None


def extract_product(text: str) -> str:
    query = text.strip()

    query = re.sub(
        r"\s+до\s+\d+(?:[.,]\d+)?\s*(?:usd|\$|eur|€|rub|₽|byn|kzt|uzs)",
        "",
        query,
        flags=re.IGNORECASE,
    )

    query = re.sub(
        r"^(мне\s+)?(нужен|нужна|нужно|хочу|ищу|найди|подбери|покажи)\s+",
        "",
        query,
        flags=re.IGNORECASE,
    )

    return query.strip(" .,!?-")


def detect_recipient(text: str):
    query = text.lower()

    recipients = {
        "девуш": "girlfriend",
        "жен": "wife",
        "муж": "husband",
        "парн": "boyfriend",
        "ребён": "child",
        "ребен": "child",
        "мам": "mother",
        "пап": "father",
    }

    for key, value in recipients.items():
        if key in query:
            return value

    return None


def build_search_request(
    text: str,
    profile: UserProfile,
) -> SearchRequest:

    budget, currency = extract_budget(text)

    currency = currency or profile.delivery.currency

    product = extract_product(text)

    return SearchRequest(
        original_query=text,
        intent=detect_intent(text),
        keywords=product.split(),
        max_price=budget,
        currency=currency,
        country=profile.delivery.country,
        city=profile.delivery.city,
        recipient=detect_recipient(text),
    )