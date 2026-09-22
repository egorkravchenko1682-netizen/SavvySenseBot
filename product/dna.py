from typing import Any

from core.models import UserContext


def build_product_dna(
    product: dict[str, Any],
    user: UserContext | None = None,
) -> dict[str, Any]:
    """
    Формирует Product DNA.

    Product DNA — структурированное описание того,
    что именно необходимо искать.

    Важный принцип:
    обязательные характеристики сохраняются отдельно
    от необязательных.
    """

    user = user or UserContext()

    attributes = dict(
        product.get(
            "attributes",
            {},
        )
    )

    # Удаляем пустые значения.
    attributes = {
        key: value
        for key, value in attributes.items()
        if value is not None
        and value != ""
    }

    required_attributes = {}

    optional_attributes = {}

    # Критические характеристики.
    #
    # Если пользователь явно указал их,
    # найденный товар должен им соответствовать.
    critical_attributes = {
        "brand",
        "model",
        "product_type",
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
    }

    for key, value in attributes.items():

        if key in critical_attributes:

            required_attributes[
                key
            ] = value

        else:

            optional_attributes[
                key
            ] = value

    # Product Identity также содержит отдельные
    # поля brand/model/product_type.
    if product.get("brand"):

        required_attributes[
            "brand"
        ] = product["brand"]

    if product.get("model"):

        required_attributes[
            "model"
        ] = product["model"]

    if product.get(
        "product_type"
    ):

        required_attributes[
            "product_type"
        ] = product[
            "product_type"
        ]

    # Условия поиска.
    condition = (
        product.get("condition")
        or "any"
    )

    # Если конкретное состояние указано
    # пользователем — оно становится обязательным.
    if condition != "any":

        required_attributes[
            "condition"
        ] = condition

    budget = None

    if product.get(
        "budget"
    ) is not None:

        budget = {
            "max":
                product.get(
                    "budget"
                ),

            "currency":
                product.get(
                    "currency"
                )
                or user.currency,
        }

    product_type = (
        product.get(
            "product_type"
        )
        or _detect_product_domain(
            product.get(
                "category"
            )
        )
    )

    exact_product = bool(
        product.get(
            "exact_product"
        )
        or product.get(
            "model"
        )
    )

    search_scope = {
        "exact_product":
            exact_product,

        "cheaper_offers":
            True,

        "similar_products":
            True,

        "international":
            True,
    }

    return {
        "name":
            product.get(
                "name"
            ),

        "brand":
            product.get(
                "brand"
            ),

        "category":
            product.get(
                "category"
            ),

        "product_type":
            product_type,

        "model":
            product.get(
                "model"
            ),

        "attributes":
            attributes,

        "required_attributes":
            required_attributes,

        "optional_attributes":
            optional_attributes,

        "budget":
            budget,

        "condition":
            condition,

        "search_scope":
            search_scope,

        "region":
            user.region,

        "currency":
            user.currency,
    }


def _detect_product_domain(
    category: str | None,
) -> str:

    if not category:
        return "general"

    category = str(
        category
    ).lower()

    electronics = {
        "smartphone",
        "laptop",
        "tablet",
        "television",
        "headphones",
        "camera",
    }

    fashion = {
        "clothing",
        "shoes",
    }

    home = {
        "furniture",
        "appliance",
    }

    tools = {
        "tool",
    }

    automotive = {
        "automotive",
    }

    if category in electronics:
        return "electronics"

    if category in fashion:
        return "fashion"

    if category in home:
        return "home"

    if category in tools:
        return "tools"

    if category in automotive:
        return "automotive"

    return "general"