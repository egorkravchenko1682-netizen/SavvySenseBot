from __future__ import annotations

from typing import Any


class CanonicalOffer:
    """Единая структура предложения товара."""

    def build(
        self,
        product: dict[str, Any] | None = None,
        attributes: dict[str, Any] | None = None,
        price: dict[str, Any] | None = None,
        shipping: dict[str, Any] | None = None,
        delivery: dict[str, Any] | None = None,
        validation: dict[str, Any] | None = None,
    ) -> dict[str, Any]:

        product = product or {}
        attributes = attributes or {}
        price = price or {}
        shipping = shipping or {}
        delivery = delivery or {}
        validation = validation or {}

        return {
            "title": product.get("title"),
            "brand": product.get("brand"),
            "category": product.get("category"),

            "attributes": attributes,

            "price": price.get("price"),
            "currency": price.get("currency"),

            "shipping_cost": shipping.get("shipping_cost"),
            "shipping_currency": shipping.get("shipping_currency"),
            "shipping_known": shipping.get("shipping_known"),
            "shipping_free": shipping.get("shipping_free"),

            "delivery_available": delivery.get("delivery_available"),
            "delivery_country": delivery.get("delivery_country"),
            "delivery_known": delivery.get("delivery_known"),

            "page_valid": validation.get("page_valid", True),
            "rejection_reason": validation.get("rejection_reason"),

        }