import re
from typing import Any, Optional


def identify_product(
    text: Optional[str] = None,
    input_type: Optional[str] = None,
) -> dict[str, Any]:
    """
    Определяет базовую идентичность товара
    из пользовательского запроса.

    Работа выполняется локально,
    без AI API и внешних сервисов.
    """

    if input_type == "photo":
        return {
            "type": "unknown",
            "name": None,
            "brand": None,
            "category": None,
            "attributes": {},
            "budget": None,
            "currency": None,
        }

    if not text:
        return {
            "type": "unknown",
            "name": None,
            "brand": None,
            "category": None,
            "attributes": {},
            "budget": None,
            "currency": None,
        }

    original_text = text.strip()
    normalized = original_text.lower()

    result = {
        "type": "product",
        "name": None,
        "brand": None,
        "category": None,
        "attributes": {},
        "budget": None,
        "currency": None,
    }

    # ---------------------------------------------------------
    # БРЕНДЫ
    # ---------------------------------------------------------

    brands = {
        "apple": "Apple",
        "iphone": "Apple",
        "samsung": "Samsung",
        "xiaomi": "Xiaomi",
        "huawei": "Huawei",
        "sony": "Sony",
        "nike": "Nike",
        "adidas": "Adidas",
        "dyson": "Dyson",
        "lenovo": "Lenovo",
        "asus": "ASUS",
        "acer": "Acer",
        "lg": "LG",
        "jbl": "JBL",
    }

    for key, brand in brands.items():
        if key in normalized:
            result["brand"] = brand
            break

    # ---------------------------------------------------------
    # КАТЕГОРИИ
    # ---------------------------------------------------------

    categories = {
        "iphone": "smartphone",
        "смартфон": "smartphone",
        "телефон": "smartphone",
        "ноутбук": "laptop",
        "laptop": "laptop",
        "планшет": "tablet",
        "наушники": "headphones",
        "телевизор": "tv",
        "часы": "smartwatch",
        "куртка": "jacket",
        "пальто": "coat",
        "кроссовки": "sneakers",
        "обувь": "shoes",
        "футболка": "tshirt",
        "джинсы": "jeans",
        "рюкзак": "backpack",
        "сумка": "bag",
        "кресло": "chair",
        "диван": "sofa",
        "холодильник": "refrigerator",
        "пылесос": "vacuum_cleaner",
        "кофемашина": "coffee_machine",
    }

    for key, category in categories.items():
        if key in normalized:
            result["category"] = category
            break

    # ---------------------------------------------------------
    # МОДЕЛЬ IPHONE
    # ---------------------------------------------------------

    iphone_match = re.search(
        r"\biphone\s*(\d{1,2})\s*"
        r"(pro\s*max|pro|max|plus)?",
        normalized,
    )

    if iphone_match:
        number = iphone_match.group(1)
        version = iphone_match.group(2)

        name = f"iPhone {number}"

        if version:
            name += f" {version.title()}"

        result["name"] = name

    # ---------------------------------------------------------
    # ПАМЯТЬ
    # ---------------------------------------------------------

    storage_match = re.search(
        r"\b(64|128|256|512|1024)\s*(gb|гб)\b",
        normalized,
    )

    if storage_match:
        result["attributes"]["storage"] = (
            f"{storage_match.group(1)} GB"
        )

    # ---------------------------------------------------------
    # ЦВЕТ
    # ---------------------------------------------------------

    colors = {
        "чёрн": "black",
        "черн": "black",
        "бел": "white",
        "красн": "red",
        "син": "blue",
        "зел": "green",
        "сер": "gray",
        "розов": "pink",
        "жёлт": "yellow",
        "желт": "yellow",
    }

    for key, color in colors.items():
        if key in normalized:
            result["attributes"]["color"] = color
            break

    # ---------------------------------------------------------
    # ПОЛ
    # ---------------------------------------------------------

    if "мужск" in normalized:
        result["attributes"]["gender"] = "men"

    elif "женск" in normalized:
        result["attributes"]["gender"] = "women"

    elif "детск" in normalized:
        result["attributes"]["gender"] = "kids"

    # ---------------------------------------------------------
    # МАТЕРИАЛ
    # ---------------------------------------------------------

    materials = {
        "кожан": "leather",
        "кожа": "leather",
        "хлопок": "cotton",
        "шерст": "wool",
        "замш": "suede",
        "деним": "denim",
    }

    for key, material in materials.items():
        if key in normalized:
            result["attributes"]["material"] = material
            break

    # ---------------------------------------------------------
    # БЮДЖЕТ
    # ---------------------------------------------------------

    budget_patterns = [
        r"(?:до|не\s*дороже|максимум|бюджет)\s*"
        r"(\d+(?:[.,]\d+)?)\s*(\$|usd|доллар\w*|€|eur|евро\w*|₽|руб\w*)?",
    ]

    for pattern in budget_patterns:
        match = re.search(pattern, normalized)

        if not match:
            continue

        amount = float(
            match.group(1).replace(",", ".")
        )

        currency_raw = match.group(2)

        currency = "USD"

        if currency_raw:
            if currency_raw in ("€", "eur") or "евро" in currency_raw:
                currency = "EUR"

            elif (
                currency_raw == "₽"
                or "руб" in currency_raw
            ):
                currency = "RUB"

            elif (
                currency_raw == "$"
                or "usd" in currency_raw
                or "доллар" in currency_raw
            ):
                currency = "USD"

        result["budget"] = amount
        result["currency"] = currency

        break

    # ---------------------------------------------------------
    # ОБЩЕЕ НАЗВАНИЕ
    # ---------------------------------------------------------

    if result["name"] is None:

        if result["category"]:
            result["name"] = result["category"]

        elif result["brand"]:
            result["name"] = result["brand"]

        else:
            result["name"] = original_text

    return result