from typing import Any


class CurrencyConverter:
    """
    Конвертер валют SAVVY SENSE.

    Пока использует локальные тестовые курсы.
    Позже источник курсов можно заменить
    на реальный API без изменения остальной архитектуры.
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

            "BYN": "BYN",
            "Br": "BYN",

            "¥": "CNY",
            "CNY": "CNY",

            "PLN": "PLN",
            "zł": "PLN",

            "TRY": "TRY",

            "JPY": "JPY",
        }

        return aliases.get(
            value,
            value,
        )

    def convert(
        self,
        amount: float,
        from_currency: str,
        to_currency: str,
    ) -> float:

        from_currency = (
            self.normalize_currency(
                from_currency
            )
        )

        to_currency = (
            self.normalize_currency(
                to_currency
            )
        )

        amount = float(amount)

        if from_currency == to_currency:
            return round(amount, 2)

        if from_currency not in self.rates_to_usd:
            raise ValueError(
                f"Unsupported currency: "
                f"{from_currency}"
            )

        if to_currency not in self.rates_to_usd:
            raise ValueError(
                f"Unsupported currency: "
                f"{to_currency}"
            )

        usd_amount = (
            amount
            * self.rates_to_usd[
                from_currency
            ]
        )

        result = (
            usd_amount
            / self.rates_to_usd[
                to_currency
            ]
        )

        return round(result, 2)