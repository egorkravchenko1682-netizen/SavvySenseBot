from typing import Any


def build_search_queries(
    product_dna: dict[str, Any],
) -> list[str]:
    """
    Формирует поисковые запросы из Product DNA.

    Критические атрибуты всегда стараемся включать
    в основной запрос.

    Дополнительные запросы нужны для расширения
    поиска, но не должны ослаблять Product Matching.
    """

    name = (
        product_dna.get(
            "name"
        )
        or ""
    ).strip()

    brand = (
        product_dna.get(
            "brand"
        )
        or ""
    ).strip()

    model = (
        product_dna.get(
            "model"
        )
        or ""
    ).strip()

    product_type = (
        product_dna.get(
            "product_type"
        )
        or ""
    ).strip()

    attributes = product_dna.get(
        "attributes",
        {},
    )

    required_attributes = (
        product_dna.get(
            "required_attributes",
            {},
        )
    )

    queries = []

    # ==========================================
    # ОСНОВНОЙ ТОЧНЫЙ ЗАПРОС
    # ==========================================

    exact_parts = []

    if brand:
        exact_parts.append(
            brand
        )

    if model:
        exact_parts.append(
            model
        )
    elif name:
        exact_parts.append(
            name
        )

    if product_type and (
        product_type
        not in exact_parts
    ):
        exact_parts.append(
            product_type
        )

    exact_parts.extend(
        _important_attribute_values(
            required_attributes
        )
    )

    exact_query = _clean_query(
        exact_parts
    )

    if exact_query:

        queries.append(
            exact_query
        )

    # ==========================================
    # BUY
    # ==========================================

    if exact_query:

        queries.append(
            f"{exact_query} buy"
        )

        queries.append(
            f"{exact_query} price"
        )

    # ==========================================
    # CHEAPER
    # ==========================================

    if exact_query:

        queries.append(
            f"{exact_query} cheaper"
        )

    # ==========================================
    # INTERNATIONAL
    # ==========================================

    if exact_query:

        queries.append(
            f"{exact_query} international"
        )

    # ==========================================
    # ДОПОЛНИТЕЛЬНЫЕ ЗАПРОСЫ
    # ==========================================

    color = attributes.get(
        "color"
    )

    material = attributes.get(
        "material"
    )

    if color and exact_query:

        queries.append(
            _clean_query(
                [
                    exact_query,
                    str(color),
                ]
            )
        )

    if material and exact_query:

        queries.append(
            _clean_query(
                [
                    exact_query,
                    str(material),
                ]
            )
        )

    # ==========================================
    # УДАЛЕНИЕ ДУБЛИКАТОВ
    # ==========================================

    unique_queries = []

    for query in queries:

        query = _clean_query(
            [query]
        )

        if not query:
            continue

        normalized = (
            query.lower()
        )

        if normalized in {
            item.lower()
            for item in unique_queries
        }:
            continue

        unique_queries.append(
            query
        )

    return unique_queries[:10]


def build_search_plan(
    product_dna: dict[str, Any],
) -> dict[str, Any]:
    """
    Создаёт полный Search Plan.
    """

    queries = build_search_queries(
        product_dna
    )

    budget = (
        product_dna.get(
            "budget"
        )
        or {}
    )

    return {
        "queries":
            queries,

        "region":
            product_dna.get(
                "region"
            ),

        "currency":
            product_dna.get(
                "currency"
            ),

        "budget":
            budget,

        "required_attributes":
            product_dna.get(
                "required_attributes",
                {},
            ),

        "optional_attributes":
            product_dna.get(
                "optional_attributes",
                {},
            ),

        "search_scope":
            product_dna.get(
                "search_scope",
                {},
            ),

        "exact_product":
            product_dna.get(
                "search_scope",
                {}
            ).get(
                "exact_product",
                False,
            ),

        "cheaper_offers":
            product_dna.get(
                "search_scope",
                {}
            ).get(
                "cheaper_offers",
                True,
            ),

        "similar_products":
            product_dna.get(
                "search_scope",
                {}
            ).get(
                "similar_products",
                True,
            ),

        "international":
            product_dna.get(
                "search_scope",
                {}
            ).get(
                "international",
                True,
            ),
    }


def _important_attribute_values(
    attributes: dict[str, Any],
) -> list[str]:

    ordered_keys = [
        "storage",
        "capacity",
        "color",
        "size",
        "material",
        "voltage",
        "quantity",
        "weight",
        "dimensions",
        "compatibility",
        "gender",
        "season",
        "condition",
    ]

    values = []

    for key in ordered_keys:

        value = attributes.get(
            key
        )

        if value is None:
            continue

        if isinstance(
            value,
            (list, tuple),
        ):

            values.extend(
                str(item)
                for item in value
                if item
            )

        else:

            values.append(
                str(value)
            )

    return values


def _clean_query(
    parts: list[str],
) -> str:

    cleaned = []

    for part in parts:

        if part is None:
            continue

        part = str(
            part
        ).strip()

        if not part:
            continue

        cleaned.append(
            part
        )

    return " ".join(
        cleaned
    )