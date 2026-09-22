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

        "product_type":
            product_type,

        "attributes": {
            key: value
            for key, value
            in attributes.items()
            if key != "keywords"
            and value is not None
        },

        "keywords":
            attributes.get(
                "keywords",
                [],
            ),

        "budget": budget,

        "currency": currency,

        "condition":
            attributes.get(
                "condition"
            ),

        "input_type":
            input_type,

        "exact_product":
            bool(
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

    Это не должно быть слишком агрессивным:
    Product DNA и AttributeExtractor получают
    отдельные структурированные атрибуты.
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

    # Убираем бюджетные ограничения.
    cleaned = re.sub(
        r"\s+(?:до|менее|max|максимум|"
        r"не дороже|за)\s+"
        r"[$€£₽]\s*\d+(?:[.,]\d+)?",
        "",
        cleaned,
        flags=re.IGNORECASE,
    )

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

    if not name:
        return None

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

    normalized = name.lower()

    for brand in known_brands:

        if re.search(
            rf"\b{re.escape(brand)}\b",
            normalized,
        ):
            return brand

    return None


def _extract_budget(
    text: str,
) -> tuple[float | None, str | None]:

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
            r"\b(\d+(?:[.,]\d+)?)\s*(?:usd|доллар(?:ов|а)?)\b",
            "USD",
        ),
        (
            r"\b(\d+(?:[.,]\d+)?)\s*(?:eur|евро)\b",
            "EUR",
        ),
        (
            r"\b(\d+(?:[.,]\d+)?)\s*(?:gbp|фунтов?)\b",
            "GBP",
        ),
        (
            r"\b(\d+(?:[.,]\d+)?)\s*(?:rub|руб(?:лей|ля)?)\b",
            "RUB",
        ),
        (
            r"\b(\d+(?:[.,]\d+)?)\s*(?:byn|белорусских\s+рублей)\b",
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
                match.group(1)
                .replace(",", ".")
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