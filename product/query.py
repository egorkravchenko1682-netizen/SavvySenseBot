from typing import Any


def build_search_queries(
    product_dna: dict[str, Any],
) -> list[str]:

    name = product_dna.get("name")
    brand = product_dna.get("brand")
    attributes = product_dna.get("attributes", {})

    if not name:
        return []

    storage = attributes.get("storage")
    color = attributes.get("color")
    material = attributes.get("material")

    parts = []

    if brand and brand.lower() not in name.lower():
        parts.append(brand)

    parts.append(name)

    if storage:
        parts.append(storage)

    base_query = " ".join(parts)

    queries = [
        base_query,
        f"{base_query} buy",
        f"{base_query} price",
        f"{base_query} cheaper",
        f"{base_query} international",
    ]

    if color:
        queries.append(
            f"{base_query} {color}"
        )

    if material:
        queries.append(
            f"{base_query} {material}"
        )

    # Убираем дубликаты
    result = []

    for query in queries:

        query = query.strip()

        if query and query not in result:
            result.append(query)

    return result


def build_search_plan(
    product_dna: dict[str, Any],
) -> dict[str, Any]:

    search_scope = product_dna.get(
        "search_scope",
        {},
    )

    return {
        "queries": build_search_queries(
            product_dna
        ),

        "region": product_dna.get(
            "region"
        ),

        "currency": product_dna.get(
            "currency"
        ),

        "budget": product_dna.get(
            "budget",
            {},
        ),

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