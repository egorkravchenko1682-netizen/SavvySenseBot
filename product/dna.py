from typing import Any, Optional


def build_product_dna(
    product: Optional[dict[str, Any]] = None,
    user: Optional[Any] = None,
) -> dict[str, Any]:
    """
    Формирует расширенное описание товара —
    Product DNA.

    Не использует AI API и внешние сервисы.
    """

    product = product or {}

    attributes = product.get("attributes", {}).copy()

    dna = {
        "brand": product.get("brand"),
        "name": product.get("name"),
        "category": product.get("category"),

        "attributes": attributes,

        "budget": {
            "max": product.get("budget"),
            "currency": product.get("currency"),
        },

        "condition": "any",

        "search_scope": {
            "exact_product": True,
            "cheaper_offers": True,
            "similar_products": True,
            "international": True,
        },

        "region": (
            getattr(user, "region", None)
            if user
            else "BY"
        ),

        "currency": (
            getattr(user, "currency", None)
            if user
            else "USD"
        ),
    }

    # Если товар конкретно определён,
    # считаем его exact-product запросом.
    if dna["name"]:
        dna["search_scope"]["exact_product"] = True

    # Определяем тип товара.
    category = dna.get("category")

    if category in {
        "smartphone",
        "laptop",
        "tablet",
        "tv",
        "smartwatch",
        "headphones",
    }:
        dna["product_type"] = "electronics"

    elif category in {
        "jacket",
        "coat",
        "sneakers",
        "shoes",
        "tshirt",
        "jeans",
        "backpack",
        "bag",
    }:
        dna["product_type"] = "fashion"

    elif category in {
        "chair",
        "sofa",
        "refrigerator",
        "vacuum_cleaner",
        "coffee_machine",
    }:
        dna["product_type"] = "home"

    else:
        dna["product_type"] = "general"

    return dna