import time
from typing import Optional

import requests


SUPPORTED_CURRENCIES = {
    "BYN",
    "RUB",
    "USD",
    "EUR",
    "GBP",
    "PLN",
    "KZT",
    "UAH",
    "CNY",
}


CURRENCY_ALIASES = {
    # USD
    "$": "USD",
    "usd": "USD",
    "доллар": "USD",
    "доллара": "USD",
    "долларов": "USD",
    "долл": "USD",

    # EUR
    "€": "EUR",
    "eur": "EUR",
    "евро": "EUR",

    # GBP
    "£": "GBP",
    "gbp": "GBP",
    "фунт": "GBP",
    "фунта": "GBP",
    "фунтов": "GBP",

    # RUB
    "₽": "RUB",
    "rub": "RUB",
    "руб": "RUB",
    "рубль": "RUB",
    "рубля": "RUB",
    "рублей": "RUB",
    "российский рубль": "RUB",
    "российских рублей": "RUB",

    # BYN
    "byn": "BYN",
    "белорусский рубль": "BYN",
    "белорусских рублей": "BYN",
    "белорусских руб": "BYN",
    "бел. руб": "BYN",

    # PLN
    "pln": "PLN",
    "злотый": "PLN",
    "злотого": "PLN",
    "злотых": "PLN",
    "зл": "PLN",

    # KZT
    "₸": "KZT",
    "kzt": "KZT",
    "тенге": "KZT",

    # UAH
    "₴": "UAH",
    "uah": "UAH",
    "гривна": "UAH",
    "гривны": "UAH",
    "гривен": "UAH",

    # CNY
    "¥": "CNY",
    "cny": "CNY",
    "юань": "CNY",
    "юаня": "CNY",
    "юаней": "CNY",
}


# Кэш курсов, чтобы не обращаться к API при каждом товаре
_rates_cache = {}
_rates_cache_time = {}

RATES_CACHE_TTL = 3600  # 1 час


def normalize_currency(currency: Optional[str]) -> Optional[str]:
    """
    Преобразует различные обозначения валюты в ISO-код.
    """

    if not currency:
        return None

    value = str(currency).strip().lower()

    if value in CURRENCY_ALIASES:
        return CURRENCY_ALIASES[value]

    upper_value = value.upper()

    if upper_value in SUPPORTED_CURRENCIES:
        return upper_value

    return None


def detect_currency_from_text(text: str) -> Optional[str]:
    """
    Определяет валюту непосредственно из текста пользователя.
    """

    if not text:
        return None

    text_lower = text.lower()

    # Более специфичные варианты проверяем раньше коротких.
    checks = [
        ("белорусских рублей", "BYN"),
        ("белорусский рубль", "BYN"),
        ("российских рублей", "RUB"),
        ("российский рубль", "RUB"),
        ("злотых", "PLN"),
        ("гривен", "UAH"),
        ("тенге", "KZT"),
        ("юаней", "CNY"),
        ("долларов", "USD"),
        ("доллара", "USD"),
        ("евро", "EUR"),
        ("рублей", "RUB"),
        ("рубля", "RUB"),
        ("рубль", "RUB"),
        ("злотый", "PLN"),
        ("гривна", "UAH"),
        ("юань", "CNY"),
        ("фунтов", "GBP"),
        ("фунт", "GBP"),
        ("byn", "BYN"),
        ("usd", "USD"),
        ("eur", "EUR"),
        ("gbp", "GBP"),
        ("rub", "RUB"),
        ("pln", "PLN"),
        ("kzt", "KZT"),
        ("uah", "UAH"),
        ("cny", "CNY"),
        ("$", "USD"),
        ("€", "EUR"),
        ("£", "GBP"),
        ("₽", "RUB"),
        ("₸", "KZT"),
        ("₴", "UAH"),
        ("¥", "CNY"),
    ]

    for marker, currency in checks:
        if marker in text_lower:
            return currency

    return None


def get_exchange_rates(base_currency: str = "USD") -> dict:
    """
    Получает курсы валют относительно базовой валюты.
    Использует кэш + резервный API.
    """

    base_currency = normalize_currency(base_currency) or "USD"

    now = time.time()

    cached_rates = _rates_cache.get(base_currency)
    cached_time = _rates_cache_time.get(base_currency, 0)

    if (
        cached_rates
        and now - cached_time < RATES_CACHE_TTL
    ):
        return cached_rates

    # Основной источник
    try:
        response = requests.get(
            "https://api.frankfurter.app/latest",
            params={
                "from": base_currency,
            },
            timeout=10,
        )

        response.raise_for_status()

        data = response.json()

        rates = data.get("rates", {})

        rates[base_currency] = 1.0

        if rates:
            _rates_cache[base_currency] = rates
            _rates_cache_time[base_currency] = now

            return rates

    except Exception as e:
        print(
            "Frankfurter currency error:",
            e,
        )

    # Резервный источник
    try:
        response = requests.get(
            f"https://open.er-api.com/v6/latest/{base_currency}",
            timeout=10,
        )

        response.raise_for_status()

        data = response.json()

        rates = data.get("rates", {})

        rates[base_currency] = 1.0

        if rates:
            _rates_cache[base_currency] = rates
            _rates_cache_time[base_currency] = now

            return rates

    except Exception as e:
        print(
            "ExchangeRate API error:",
            e,
        )

    # Хотя бы возвращаем базовую валюту
    return {
        base_currency: 1.0
    }


def convert_currency(
    amount: float,
    from_currency: str,
    to_currency: str,
) -> Optional[float]:
    """
    Конвертирует сумму из одной валюты в другую.
    """

    if amount is None:
        return None

    from_currency = normalize_currency(
        from_currency
    )

    to_currency = normalize_currency(
        to_currency
    )

    if not from_currency or not to_currency:
        return None

    try:
        amount = float(amount)
    except (
        TypeError,
        ValueError,
    ):
        return None

    if from_currency == to_currency:
        return amount

    rates = get_exchange_rates(
        from_currency
    )

    rate = rates.get(to_currency)

    if rate is None:
        print(
            "Currency rate not found:",
            from_currency,
            "->",
            to_currency,
        )
        return None

    return amount * float(rate)


def convert_to_budget_currency(
    price: float,
    price_currency: str,
    budget_currency: str,
) -> Optional[float]:
    """
    Переводит цену товара в валюту бюджета.
    """

    return convert_currency(
        price,
        price_currency,
        budget_currency,
    )


def is_within_budget(
    price: float,
    price_currency: str,
    budget: float,
    budget_currency: str,
) -> bool:
    """
    Проверяет, укладывается ли товар в бюджет.
    """

    converted_price = convert_to_budget_currency(
        price,
        price_currency,
        budget_currency,
    )

    if converted_price is None:
        return False

    return converted_price <= budget


def format_money(
    amount: float,
    currency: str,
) -> str:
    """
    Красивое отображение денег.
    """

    currency = normalize_currency(currency)

    symbols = {
        "BYN": "Br",
        "RUB": "₽",
        "USD": "$",
        "EUR": "€",
        "GBP": "£",
        "PLN": "zł",
        "KZT": "₸",
        "UAH": "₴",
        "CNY": "¥",
    }

    symbol = symbols.get(
        currency,
        currency or "",
    )

    if currency in {
        "USD",
        "EUR",
        "GBP",
    }:
        return f"{symbol}{amount:.2f}"

    if currency == "BYN":
        return f"{amount:.2f} Br"

    if currency == "RUB":
        return f"{amount:.2f} ₽"

    if currency == "PLN":
        return f"{amount:.2f} zł"

    if currency == "KZT":
        return f"{amount:.2f} ₸"

    if currency == "UAH":
        return f"{amount:.2f} ₴"

    if currency == "CNY":
        return f"{amount:.2f} ¥"

    return f"{amount:.2f} {currency or ''}".strip()