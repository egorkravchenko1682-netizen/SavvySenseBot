from typing import Any


def build_search_queries(
    product_dna: dict[str, Any],
) -> list[str]:
    """
    Формирует поисковые запросы из Product DNA.

    ВАЖНО:
    Search Query Builder отвечает за поиск кандидатов,
    а не за окончательное определение совпадения.

    Поэтому основной запрос не перегружается всеми
    возможными атрибутами. Строгая проверка выполняется
    позже через ProductMatcher.
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

    queries: list[str] = []

    # ==================================================
    # БАЗОВОЕ НАЗВАНИЕ
    # ==================================================

    base_name = ""

    if brand and model:

        base_name = _clean_query(
            [
                brand,
                model,
            ]
        )

    elif model:

        base_name = model

    elif name:

        base_name = _clean_query(
            [
                name,
            ]
        )

    # ==================================================
    # КРИТИЧЕСКИЕ АТРИБУТЫ
    # ==================================================

    critical_values = (
        _important_attribute_values(
            required_attributes
        )
    )

    # Основной точный запрос.
    #
    # Например:
    #
    # Apple iPhone 15 Pro Max 256 GB
    #
    # а не:
    #
    # iPhone 15 Pro Max smartphone 256 GB
    #
    # Тип товара не нужен поисковику,
    # поскольку Matcher проверит его позже.

    if base_name:

        exact_query = _clean_query(
            [
                base_name,
                *critical_values,
            ]
        )

        if exact_query:
            queries.append(
                exact_query
            )

    # ==================================================
    # ЗАПРОС БЕЗ ДОПОЛНИТЕЛЬНЫХ АТРИБУТОВ
    # ==================================================

    if base_name:

        queries.append(
            base_name
        )

    # ==================================================
    # BUY
    # ==================================================

    if base_name:

        buy_query = _clean_query(
            [
                base_name,
                *critical_values,
                "buy",
            ]
        )

        if buy_query:
            queries.append(
                buy_query
            )

    # ==================================================
    # PRICE
    # ==================================================

    if base_name:

        price_query = _clean_query(
            [
                base_name,
                *critical_values,
                "price",
            ]
        )

        if price_query:
            queries.append(
                price_query
            )

    # ==================================================
    # CHEAPER
    # ==================================================

    if base_name:

        cheaper_query = _clean_query(
            [
                base_name,
                *critical_values,
                "cheaper",
            ]
        )

        if cheaper_query:
            queries.append(
                cheaper_query
            )

    # ==================================================
    # INTERNATIONAL
    # ==================================================

    if base_name:

        international_query = _clean_query(
            [
                base_name,
                *critical_values,
                "international",
            ]
        )

        if international_query:
            queries.append(
                international_query
            )

    # ==================================================
    # АТРИБУТНЫЕ ВАРИАНТЫ
    # ==================================================

    color = attributes.get(
        "color"
    )

    material = attributes.get(
        "material"
    )

    size = attributes.get(
        "size"
    )

    capacity = attributes.get(
        "capacity"
    )

    # Цвет.
    if color and base_name:

        queries.append(
            _clean_query(
                [
                    base_name,
                    str(color),
                ]
            )
        )

    # Материал.
    if material and base_name:

        queries.append(
            _clean_query(
                [
                    base_name,
                    str(material),
                ]
            )
        )

    # Размер.
    if size and base_name:

        queries.append(
            _clean_query(
                [
                    base_name,
                    str(size),
                ]
            )
        )

    # Ёмкость.
    if capacity and base_name:

        queries.append(
            _clean_query(
                [
                    base_name,
                    str(capacity),
                ]
            )
        )

    # ==================================================
    # ДЕДУПЛИКАЦИЯ
    # ==================================================

    return _unique_queries(
        queries
    )


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

    search_scope = (
        product_dna.get(
            "search_scope",
            {},
        )
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
            search_scope,

        "exact_product":
            search_scope.get(
                "exact_product",
                False,
            ),

        "cheaper_offers":
            search_scope.get(
                "cheaper_offers",
                True,
            ),

        "similar_products":
            search_scope.get(
                "similar_products",
                True,
            ),

        "international":
            search_scope.get(
                "international",
                True,
            ),
    }


def _important_attribute_values(
    attributes: dict[str, Any],
) -> list[str]:
    """
    Возвращает атрибуты, которые действительно
    полезно передавать поисковику.

    Не добавляем category/product_type автоматически:
    эти параметры используются преимущественно
    для последующей валидации результата.
    """

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

            for item in value:

                if item:

                    values.append(
                        str(item)
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


def _unique_queries(
    queries: list[str],
) -> list[str]:

    result = []

    seen = set()

    for query in queries:

        query = _clean_query(
            [query]
        )

        if not query:
            continue

        normalized = (
            query.lower()
            .strip()
        )

        if normalized in seen:
            continue

        seen.add(
            normalized
        )

        result.append(
            query
        )

    return result[:10]