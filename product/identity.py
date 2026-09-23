import re
from typing import Any

from .attributes import AttributeExtractor


_ATTRIBUTE_EXTRACTOR = AttributeExtractor()


def identify_product(
    text: str | None = None,
    input_type: str | None = None,
) -> dict[str, Any]:
    """
    Формирует Product Identity из пользовательского запроса.

    AttributeExtractor используется как универсальный слой
    извлечения характеристик.

    Неизвестные параметры не выдумываются.
    """

    text = (text or "").strip()

    attributes = _ATTRIBUTE_EXTRACTOR.extract(
        text
    )

    name = _extract_product_name(
        text=text,
        attributes=attributes,
    )

    brand = (
        attributes.get("brand")
        or _extract_brand_from_name(name)
    )

    category = (
        attributes.get("category")
        or "general"
    )

    product_type = (
        attributes.get("product_type")
    )

    model = attributes.get(
        "model"
    )

    budget, currency = _extract_budget(
        text
    )

    return {
        "name": name,

        "brand": brand,

        "category": category,

        "model": model,

        "product_type": product_type,

        "attributes": {
            key: value
            for key, value in attributes.items()
            if key != "keywords"
            and value is not None
        },

        "keywords": attributes.get(
            "keywords",
            [],
        ),

        "budget": budget,

        "currency": currency,

        "condition": attributes.get(
            "condition"
        ),

        "input_type": input_type,

        "exact_product": bool(
            model
            or name
        ),
    }


def _extract_product_name(
    text: str,
    attributes: dict[str, Any],
) -> str | None:
    """
    Формирует название товара без служебных частей
    запроса и бюджета.
    """

    if not text:
        return None

    cleaned = text.strip()

    # Убираем типичные вводные конструкции.
    cleaned = re.sub(
        r"^\s*(найди|найдите|нужен|нужна|нужно|"
        r"хочу|ищу|купить|подбери|подберите|"
        r"покажи|покажите)\s+",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )

    # Убираем бюджетные ограничения с символом валюты.
    cleaned = re.sub(
        r"\s+(?:до|менее|max|максимум|"
        r"не дороже|за)\s+"
        r"[$€£₽]\s*\d+(?:[.,]\d+)?",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )

    # Убираем бюджетные ограничения с названием валюты.
    cleaned = re.sub(
        r"\s+(?:до|менее|max|максимум|"
        r"не дороже|за)\s+"
        r"\d+(?:[.,]\d+)?\s*"
        r"(?:usd|eur|gbp|rub|byn|cny|pln|"
        r"долларов|долл|евро|рублей|руб|"
        r"белорусских\s+рублей)",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )

    cleaned = re.sub(
        r"\s+",
        " ",
        cleaned,
    ).strip()

    if not cleaned:
        return None

    return cleaned


def _extract_brand_from_name(
    name: str | None,
) -> str | None:
    """
    Определяет бренд по названию товара.

    Используются два уровня:

    1. Явное название бренда:
       "Apple iPhone 15 Pro"

    2. Устойчивый маркер бренда:
       "iPhone 15 Pro" -> Apple
       "Galaxy S24" -> Samsung
       "Pixel 9" -> Google

    Неизвестный бренд не угадывается.
    """

    if not name:
        return None

    normalized = name.lower().strip()

    # Явные названия брендов.
    known_brands = {
        "apple",
        "samsung",
        "xiaomi",
        "google",
        "oneplus",
        "huawei",
        "honor",
        "sony",
        "lg",
        "lenovo",
        "asus",
        "acer",
        "hp",
        "dell",
        "msi",
        "microsoft",
        "nike",
        "adidas",
        "puma",
        "reebok",
        "zara",
        "uniqlo",
        "bosch",
        "philips",
        "dyson",
        "makita",
        "dewalt",
        "milwaukee",
        "ikea",
        "lego",
        "logitech",
        "jbl",
        "canon",
        "nikon",
        "fujifilm",
        "gopro",
        "dji",
        "roborock",
        "dreame",
        "ecovacs",
    }

    for brand in known_brands:
        if re.search(
            rf"\b{re.escape(brand)}\b",
            normalized,
        ):
            return brand

    # Семантические маркеры брендов.
    #
    # Например:
    # iPhone -> Apple
    # Galaxy -> Samsung
    # Pixel -> Google
    brand_markers = {
        "apple": {
            "iphone",
            "ipad",
            "macbook",
            "imac",
            "airpods",
            "apple watch",
        },
        "samsung": {
            "galaxy",
            "galaxy s",
            "galaxy a",
            "galaxy z",
            "galaxy note",
        },
        "google": {
            "pixel",
            "pixel pro",
            "pixel fold",
        },
        "xiaomi": {
            "redmi",
            "poco",
            "mi phone",
        },
        "sony": {
            "playstation",
            "xperia",
        },
        "microsoft": {
            "surface",
            "xbox",
        },
        "dyson": {
            "supersonic",
            "airwrap",
            "v15 detect",
        },
    }

    for brand, markers in brand_markers.items():

        for marker in markers:

            if re.search(
                rf"\b{re.escape(marker)}\b",
                normalized,
            ):
                return brand

    return None


def _extract_budget(
    text: str,
) -> tuple[float | None, str | None]:
    """
    Извлекает бюджет только тогда,
    когда число явно используется как ограничение.
    """

    if not text:
        return None, None

    currency_patterns = [
        (
            r"[$]\s*(\d+(?:[.,]\d+)?)",
            "USD",
        ),
        (
            r"[€]\s*(\d+(?:[.,]\d+)?)",
            "EUR",
        ),
        (
            r"[£]\s*(\d+(?:[.,]\d+)?)",
            "GBP",
        ),
        (
            r"[₽]\s*(\d+(?:[.,]\d+)?)",
            "RUB",
        ),
        (
            r"\b(\d+(?:[.,]\d+)?)\s*"
            r"(?:usd|доллар(?:ов|а)?)\b",
            "USD",
        ),
        (
            r"\b(\d+(?:[.,]\d+)?)\s*"
            r"(?:eur|евро)\b",
            "EUR",
        ),
        (
            r"\b(\d+(?:[.,]\d+)?)\s*"
            r"(?:gbp|фунтов?)\b",
            "GBP",
        ),
        (
            r"\b(\d+(?:[.,]\d+)?)\s*"
            r"(?:rub|руб(?:лей|ля)?)\b",
            "RUB",
        ),
        (
            r"\b(\d+(?:[.,]\d+)?)\s*"
            r"(?:byn|белорусских\s+рублей)\b",
            "BYN",
        ),
    ]

    for pattern, currency in currency_patterns:

        match = re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )

        if not match:
            continue

        try:
            value = float(
                match.group(1).replace(
                    ",",
                    ".",
                )
            )

        except (
            TypeError,
            ValueError,
        ):
            continue

        # Считаем число бюджетом только если
        # оно используется как ограничение.
        prefix = text[
            max(
                0,
                match.start() - 12,
            ):
            match.start()
        ].lower()

        if any(
            word in prefix
            for word in (
                "до",
                "менее",
                "максимум",
                "max",
                "не дороже",
            )
        ):
            return value, currency

    return None, None