from dataclasses import dataclass, field
from typing import Any


@dataclass
class Seller:
    name: str | None = None
    rating: float | None = None
    reviews_count: int | None = None


@dataclass
class Money:
    amount: float | None = None
    currency: str | None = None


@dataclass
class Shipping:
    available: bool | None = None
    amount: float | None = None
    currency: str | None = None
    days_min: int | None = None
    days_max: int | None = None


@dataclass
class ProductData:
    title: str = ""
    brand: str | None = None
    model: str | None = None
    product_type: str | None = None
    category: str | None = None
    attributes: dict[str, Any] = field(default_factory=dict)


@dataclass
class CanonicalOffer:
    source: str
    url: str

    product: ProductData

    price: Money = field(
        default_factory=Money
    )

    shipping: Shipping = field(
        default_factory=Shipping
    )

    seller: Seller = field(
        default_factory=Seller
    )

    availability: bool = True

    condition: str = "unknown"

    raw: dict[str, Any] = field(
        default_factory=dict
    )

    def total_known_cost(
        self,
    ) -> float | None:

        if self.price.amount is None:
            return None

        total = self.price.amount

        if (
            self.shipping.amount is not None
        ):
            total += self.shipping.amount

        return total