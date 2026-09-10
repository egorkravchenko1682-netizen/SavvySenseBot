import requests


# Валюты, которые поддерживает SAVVY SENSE
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


def normalize_currency(currency: str | None) -> str | None:
    """
    Приводит разные обозначения валюты
    к единому коду.
    """

    if not currency:
        return None

    value = currency.strip().lower()

    aliases = {
        "$": "USD",
        "usd": "USD",
        "доллар": "USD",
        "доллара": "USD",
        "долларов": "USD",

        "€": "EUR",
        "eur": "EUR",
        "евро": "EUR",

        "£": "GBP",
        "gbp": "GBP",
        "фунт": "GBP",
        "фунтов": "GBP",

        "₽": "RUB",
        "rub": "RUB",
        "руб": "RUB",
        "рубль": "RUB",
        "рубля": "RUB",
        "рублей": "RUB",

        "р": "BYN",
        "byn": "BYN",
        "белорусский рубль": "BYN",
        "белорусских рублей": "BYN",
        "белорусских руб": "BYN",

        "pln": "PLN",
        "злотый": "PLN",
        "злотых": "PLN",

        "kzt": "KZT",
        "₸": "KZT",
        "тенге": "KZT",

        "uah": "UAH",
        "₴": "UAH",
        "гривна": "UAH",
        "гривен": "UAH",

        "cny": "CNY",
        "¥": "CNY",
        "юань": "CNY",
        "юаней": "CNY",
    }

    if value in aliases:
        return aliases[value]

    value = value.upper()

    if value in SUPPORTED_CURRENCIES:
        return value

    return None


def get_exchange_rates(
    base_currency: str = "USD"
) -> dict:
    """
    Получает актуальные курсы валют
    относительно базовой валюты.
    """

    base_currency = normalize_currency(
        base_currency
    )

    if not base_currency:
        base_currency = "USD"

    url = (
        "https://api.frankfurter.app/latest"
    )

    params = {
        "from": base_currency
    }

    try:
        response = requests.get(
            url,
            params=params,
            timeout=10,
        )

        response.raise_for_status()

        data = response.json()

        rates = data.get(
            "rates",
            {}
        )

        rates[base_currency] = 1.0

        return rates

    except Exception as e:

        print(
            "Currency API error:",
            e
        )

        return {
            base_currency: 1.0
        }


def convert_currency(
    amount: float,
    from_currency: str,
    to_currency: str,
) -> float | None:
    """
    Конвертирует сумму из одной валюты
    в другую.
    """

    from_currency = normalize_currency(
        from_currency
    )

    to_currency = normalize_currency(
        to_currency
    )

    if not from_currency or not to_currency:
        return None

    if from_currency == to_currency:
        return float(amount)

    rates = get_exchange_rates(
        from_currency
    )

    rate = rates.get(
        to_currency
    )

    if rate is None:
        return None

    return float(amount) * float(rate)


def is_within_budget(
    price: float,
    price_currency: str,
    budget: float,
    budget_currency: str,
) -> bool:
    """
    Проверяет, находится ли товар
    в пределах бюджета пользователя.
    """

    converted_price = convert_currency(
        price,
        price_currency,
        budget_currency,
    )

    if converted_price is None:
        return False

    return converted_price <= budget


def convert_to_budget_currency(
    price: float,
    price_currency: str,
    budget_currency: str,
) -> float | None:
    """
    Возвращает цену товара
    в валюте бюджета пользователя.
    """

    return convert_currency(
        price,
        price_currency,
        budget_currency,
    )