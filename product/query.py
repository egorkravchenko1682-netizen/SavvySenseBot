from typing import Any


def build_search_queries(
    product_dna: dict[str, Any],
) -> list[str]:
    """
    Создаёт набор поисковых запросов
    на основе Product DNA.

    Не использует AI API и внешние сервисы.
    """

    name = product_dna.get("name")
    brand = product_dna.get("brand")
    category = product_dna.get("category")
    attributes = product_dna.get("attributes", {})

    if not name:
        return []

    storage = attributes.get("storage")
    color = attributes.get("color")
    material = attributes.get("material")
    gender = attributes.get("gender")

    # Базовое название товара
    parts = []

    if brand and brand.lower() not in name.lower():
        parts.append(brand)

    parts.append(name)

    if storage:
        parts.append(storage)

    base_query = " ".join(parts)

    queries = []

    # 1. Точный товар
    queries.append(base_query)

    # 2. Покупка
    queries.append(
        f"{base_query} buy"
    )

    # 3. Цена
    queries.append(
        f"{base_query} price"
    )

    # 4. Поиск дешевле
    queries.append(
        f"{base_query} cheaper"
    )

    # 5. Международный поиск
    queries.append(
        f"{base_query} international"
    )

    # Дополнительные характеристики
    if color:
        queries.append(
            f"{base_query} {color}"
        )

    if material:
        queries.append(
            f"{base_query} {material}"
        )

    if gender:
        queries.append(
            f"{base_query} {gender}"
        )

    # Убираем дубликаты,
    # сохраняя порядок.
    unique_queries = []

    for query in queries:
        query = query.strip()

        if query and query not in unique_queries:
            unique_queries.append(query)

    return unique_queries


def build_search_plan(
    product_dna: dict[str, Any],
) -> dict[str, Any]:
    """
    Формирует полный план будущего поиска.
    """

    queries = build_search_queries(
        product_dna
    )

    search_scope = product_dna.get(
        "search_scope",
        {},
    )

    budget = product_dna.get(
        "budget",
        {},
    )

    return {
        "queries": queries,

        "region": product_dna.get(
            "region"
        ),

        "currency": product_dna.get(
            "currency"
        ),

        "budget": budget,

        "exact_product": search_scope.get(
            "exact_product",
            True,
        ),

        "cheaper_offers": search_scope.get(
            "cheaper_offers",
            True,
        ),

        "similar_products": search_scope.get(
            "similar_products",
            True,
        ),

        "international": search_scope.get(
            "international",
            True,
        ),
    }