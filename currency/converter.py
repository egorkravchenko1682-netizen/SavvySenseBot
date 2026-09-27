from typing import Any


class CurrencyConverter:
    """
    Конвертер валют SAVVY SENSE.

    Использует локальные курсы (относительно USD). Курсы приблизительные
    и предназначены для сравнения предложений между регионами, а не для
    точных финансовых расчётов. Источник курсов можно заменить на
    реальный API (ЦБ РФ, НБ РБ, exchangerate.host и т.д.) без изменения
    остальной архитектуры — весь код, использующий конвертер, обращается
    только к методу `convert()`.
    """

    def __init__(
        self,
        rates_to_usd: dict[str, float] | None = None,
    ):
        self.rates_to_usd = rates_to_usd or {
            "USD": 1.0,
            "EUR": 1.10,
            "GBP": 1.27,
            "RUB": 0.011,
            "BYN": 0.31,
            "CNY": 0.14,
            "PLN": 0.26,
            "TRY": 0.027,
            "JPY": 0.0068,
            # Валюты стран СНГ из README (приблизительные курсы).
            "KZT": 0.0019,
            "UZS": 0.000078,
            "AMD": 0.0026,
            "AZN": 0.59,
            "MDL": 0.056,
            "KGS": 0.011,
        }

    def normalize_currency(
        self,
        currency: Any,
    ) -> str:

        if not currency:
            return "USD"

        value = str(currency).upper().strip()

        aliases = {
            "$": "USD",
            "US$": "USD",
            "USD": "USD",
            "€": "EUR",
            "EUR": "EUR",
            "£": "GBP",
            "GBP": "GBP",
            "₽": "RUB",
            "RUB": "RUB",
            "RUR": "RUB",
            "BYN": "BYN",
            "BR": "BYN",
            "¥": "CNY",
            "CNY": "CNY",
            "RMB": "CNY",
            "PLN": "PLN",
            "ZŁ": "PLN",
            "TRY": "TRY",
            "JPY": "JPY",
            "KZT": "KZT",
            "₸": "KZT",
            "UZS": "UZS",
            "AMD": "AMD",
            "AZN": "AZN",
            "MDL": "MDL",
            "KGS": "KGS",
        }

        return aliases.get(value, value)

    def convert(
        self,
        amount: float,
        from_currency: str,
        to_currency: str,
    ) -> float:

        from_currency = self.normalize_currency(from_currency)
        to_currency = self.normalize_currency(to_currency)

        amount = float(amount)

        if from_currency == to_currency:
            return round(amount, 2)

        if from_currency not in self.rates_to_usd:
            raise ValueError(f"Unsupported currency: {from_currency}")

        if to_currency not in self.rates_to_usd:
            raise ValueError(f"Unsupported currency: {to_currency}")

        usd_amount = amount * self.rates_to_usd[from_currency]
        result = usd_amount / self.rates_to_usd[to_currency]

        return round(result, 2)
